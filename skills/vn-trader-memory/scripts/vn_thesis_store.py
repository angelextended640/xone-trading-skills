"""VN Trader Memory — thesis CRUD with VND currency + lot-100 + fee/tax accounting.

Adapted from skills/trader-memory-core/scripts/thesis_store.py with these
VN-specific behaviours baked in:

  * Currency: all monetary fields are VND (no USD anywhere).
  * Lot rule: ``position.shares`` must be a positive multiple of 100.
  * Default review interval: 5 days (T+2.5 settlement + 2 sessions to assess).
  * Realised P&L: ``outcome.broker_fee_vnd`` + ``outcome.sale_tax_vnd`` are
    computed alongside gross, so ``net_pnl_vnd = gross - fee - tax``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import tempfile
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, FormatChecker

logger = logging.getLogger(__name__)

# -- Constants ----------------------------------------------------------------

_STATUS_ORDER = ["IDEA", "ENTRY_READY", "ACTIVE", "CLOSED", "INVALIDATED"]
_TERMINAL_STATUSES = {"CLOSED", "INVALIDATED"}

_TYPE_ABBR = {
    "dividend_income": "div",
    "growth_momentum": "grw",
    "mean_reversion": "rev",
    "earnings_drift": "ern",
    "pivot_breakout": "pvt",
}
_VALID_THESIS_TYPES = set(_TYPE_ABBR.keys())

INDEX_FILE = "_index.json"

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "thesis.schema.json"
_SCHEMA: dict | None = None
_VALID_EXIT_REASONS = {
    "stop_hit",
    "target_hit",
    "time_stop",
    "invalidated",
    "manual",
    "trailing_stop",
}

# VN broker fee + sale tax constants. Round-trip retail defaults — override
# via close() arguments when a specific broker has been negotiated lower.
DEFAULT_BROKER_FEE_PCT = 0.0015  # 0.15% each side
DEFAULT_SALE_TAX_PCT = 0.001  # 0.1% on sell proceeds only
DEFAULT_REVIEW_INTERVAL_DAYS = 5  # T+2.5 + 2 sessions

_FORMAT_CHECKER = FormatChecker()


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@_FORMAT_CHECKER.checks("date-time", raises=ValueError)
def _check_datetime(value):
    if not isinstance(value, str):
        return True
    if " " in value:
        raise ValueError(f"date-time must use 'T' separator: {value}")
    normalized = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        raise ValueError(f"Invalid date-time: {value}")
    if dt.tzinfo is None:
        raise ValueError(f"date-time must include timezone offset: {value}")
    return True


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@_FORMAT_CHECKER.checks("date", raises=ValueError)
def _check_date(value):
    if not isinstance(value, str):
        return True
    if not _DATE_RE.match(value):
        raise ValueError(f"date must be YYYY-MM-DD (zero-padded): {value}")
    date.fromisoformat(value)
    return True


# -- Helpers ------------------------------------------------------------------


def _get_schema() -> dict:
    global _SCHEMA
    if _SCHEMA is None:
        with open(_SCHEMA_PATH, encoding="utf-8") as f:
            _SCHEMA = json.load(f)
    return _SCHEMA


def _validate_thesis(thesis: dict) -> None:
    """Schema + business invariants. Raises ValueError on any violation."""
    schema = _get_schema()
    validator = Draft7Validator(schema, format_checker=_FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(thesis), key=lambda e: list(e.path))
    if errors:
        raise ValueError(f"Schema validation failed: {errors[0].message}")

    status = thesis.get("status")

    if status == "ACTIVE":
        entry = thesis.get("entry", {})
        if entry.get("actual_price") is None:
            raise ValueError("ACTIVE thesis requires entry.actual_price")
        if entry.get("actual_date") is None:
            raise ValueError("ACTIVE thesis requires entry.actual_date")

    if status == "CLOSED":
        exit_data = thesis.get("exit", {})
        if exit_data.get("actual_price") is None:
            raise ValueError("CLOSED thesis requires exit.actual_price")
        if exit_data.get("actual_date") is None:
            raise ValueError("CLOSED thesis requires exit.actual_date")
        if exit_data.get("exit_reason") not in _VALID_EXIT_REASONS:
            raise ValueError(f"Invalid exit_reason: {exit_data.get('exit_reason')}")
        entry_date = thesis.get("entry", {}).get("actual_date")
        exit_date = exit_data.get("actual_date")
        if entry_date and exit_date and _parse_dt(exit_date) < _parse_dt(entry_date):
            raise ValueError("exit.actual_date must be >= entry.actual_date")

    if status == "INVALIDATED":
        exit_data = thesis.get("exit", {})
        reason = exit_data.get("exit_reason")
        if reason is not None and reason != "invalidated":
            raise ValueError(
                f"INVALIDATED thesis must have exit_reason='invalidated', got '{reason}'"
            )

    history = thesis.get("status_history", [])
    for i in range(1, len(history)):
        prev_at = history[i - 1].get("at", "")
        curr_at = history[i].get("at", "")
        if prev_at and curr_at and _parse_dt(curr_at) < _parse_dt(prev_at):
            raise ValueError(
                f"status_history[{i}].at ({curr_at}) is before "
                f"status_history[{i - 1}].at ({prev_at})"
            )
    if history and history[-1]["status"] != thesis["status"]:
        raise ValueError(
            f"status_history[-1].status ({history[-1]['status']}) "
            f"!= thesis.status ({thesis['status']})"
        )


def _now_iso() -> str:
    # Use Asia/Ho_Chi_Minh-ish offset for display; the schema accepts any tz.
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _generate_thesis_id(ticker: str, thesis_type: str, date_str: str) -> str:
    abbr = _TYPE_ABBR.get(thesis_type)
    if abbr is None:
        raise ValueError(
            f"Unknown thesis_type: {thesis_type}. Must be one of {sorted(_VALID_THESIS_TYPES)}"
        )
    salt = uuid.uuid4().hex[:8]
    hash4 = hashlib.sha256(f"{ticker}_{thesis_type}_{date_str}_{salt}".encode()).hexdigest()[:4]
    return f"th_{ticker.lower()}_{abbr}_{date_str}_{hash4}"


def _compute_origin_fingerprint(thesis_data: dict) -> str:
    parts = [
        thesis_data.get("ticker", ""),
        thesis_data.get("thesis_type", ""),
        thesis_data.get("thesis_statement", ""),
        thesis_data.get("_source_date", ""),
    ]
    origin = thesis_data.get("origin", {})
    parts.append(origin.get("skill", ""))
    raw = origin.get("raw_provenance", {})
    if raw:
        parts.append(json.dumps(raw, sort_keys=True, default=str))
    content = "|".join(parts)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _find_by_fingerprint(state_dir: Path, fingerprint: str) -> str | None:
    index = _load_index(state_dir)
    for tid, entry in index.get("theses", {}).items():
        if entry.get("origin_fingerprint") == fingerprint:
            return tid
    for yaml_path in state_dir.glob("th_*.yaml"):
        try:
            thesis = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if thesis and thesis.get("origin_fingerprint") == fingerprint:
                return thesis["thesis_id"]
        except (OSError, yaml.YAMLError, KeyError):
            continue
    return None


def _atomic_write_yaml(path: Path, data: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _atomic_write_json(path: Path, data: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _load_index(state_dir: Path) -> dict:
    idx_path = state_dir / INDEX_FILE
    if idx_path.exists():
        with open(idx_path, encoding="utf-8") as f:
            return json.load(f)
    return {"version": 1, "theses": {}}


def _save_index(state_dir: Path, index: dict) -> None:
    _atomic_write_json(state_dir / INDEX_FILE, index)


def _load_thesis(state_dir: Path, thesis_id: str) -> dict:
    path = state_dir / f"{thesis_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Thesis not found: {thesis_id}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save_thesis(state_dir: Path, thesis: dict) -> None:
    _validate_thesis(thesis)
    path = state_dir / f"{thesis['thesis_id']}.yaml"
    _atomic_write_yaml(path, thesis)


def _default_thesis() -> dict:
    return {
        "thesis_id": None,
        "ticker": None,
        "exchange": None,
        "created_at": None,
        "updated_at": None,
        "thesis_type": None,
        "setup_type": None,
        "catalyst": None,
        "status": "IDEA",
        "status_history": [],
        "thesis_statement": None,
        "evidence": [],
        "kill_criteria": [],
        "confidence": None,
        "confidence_score": None,
        "origin_fingerprint": None,
        "entry": {
            "target_price": None,
            "stop_loss": None,
            "conditions": [],
            "actual_price": None,
            "actual_date": None,
            "setup_type": None,
        },
        "exit": {
            "stop_loss": None,
            "take_profit": None,
            "take_profit_rr": None,
            "time_stop_days": None,
            "actual_price": None,
            "actual_date": None,
            "exit_reason": None,
        },
        "position": None,
        "market_context": None,
        "monitoring": {
            "review_interval_days": DEFAULT_REVIEW_INTERVAL_DAYS,
            "next_review_date": None,
            "last_review_date": None,
            "review_status": "OK",
            "alerts": [],
        },
        "origin": {
            "skill": None,
            "output_file": None,
            "screening_grade": None,
            "screening_score": None,
            "raw_provenance": {},
        },
        "linked_reports": [],
        "outcome": None,
    }


def _project_index_fields(thesis: dict) -> dict:
    created_date = thesis["created_at"][:10] if thesis["created_at"] else None
    updated_at = thesis.get("updated_at") or thesis["created_at"]
    updated_date = updated_at[:10] if updated_at else None
    return {
        "ticker": thesis["ticker"],
        "exchange": thesis.get("exchange"),
        "status": thesis["status"],
        "thesis_type": thesis["thesis_type"],
        "created_at": created_date,
        "updated_at": updated_date,
        "next_review_date": thesis.get("monitoring", {}).get("next_review_date"),
        "review_status": thesis.get("monitoring", {}).get("review_status", "OK"),
        "origin_fingerprint": thesis.get("origin_fingerprint"),
    }


def _update_index_entry(index: dict, thesis: dict) -> None:
    index["theses"][thesis["thesis_id"]] = _project_index_fields(thesis)


# -- Public API ---------------------------------------------------------------


def register(state_dir: Path, thesis_data: dict) -> str:
    """Register a new IDEA thesis. Idempotent on origin fingerprint."""
    required = ["ticker", "thesis_type", "thesis_statement"]
    for field in required:
        if not thesis_data.get(field):
            raise ValueError(f"Missing required field: {field}")

    if thesis_data["thesis_type"] not in _VALID_THESIS_TYPES:
        raise ValueError(
            f"Invalid thesis_type: {thesis_data['thesis_type']}. "
            f"Must be one of {sorted(_VALID_THESIS_TYPES)}"
        )

    origin = thesis_data.get("origin", {})
    if not origin.get("skill"):
        raise ValueError("Missing required field: origin.skill")
    if not origin.get("output_file"):
        raise ValueError("Missing required field: origin.output_file")

    state_dir.mkdir(parents=True, exist_ok=True)
    fingerprint = _compute_origin_fingerprint(thesis_data)

    thesis = _default_thesis()
    now = _now_iso()

    source_date = thesis_data.get("_source_date")
    if source_date:
        date_str = source_date.replace("-", "")
        created_at = f"{source_date}T00:00:00+00:00"
        source_base = created_at
    else:
        date_str = _today_str()
        created_at = now
        source_base = now
    thesis_id = _generate_thesis_id(thesis_data["ticker"], thesis_data["thesis_type"], date_str)

    thesis["thesis_id"] = thesis_id
    thesis["ticker"] = thesis_data["ticker"].upper()
    thesis["exchange"] = thesis_data.get("exchange")
    thesis["created_at"] = created_at
    thesis["updated_at"] = now
    thesis["thesis_type"] = thesis_data["thesis_type"]
    thesis["origin_fingerprint"] = fingerprint
    thesis["status"] = "IDEA"
    thesis["status_history"] = [
        {
            "status": "IDEA",
            "at": source_base,
            "reason": thesis_data.get("_register_reason", "registered"),
        }
    ]

    for key in [
        "setup_type",
        "catalyst",
        "thesis_statement",
        "evidence",
        "kill_criteria",
        "confidence",
        "confidence_score",
    ]:
        if key in thesis_data:
            thesis[key] = thesis_data[key]

    if "entry" in thesis_data:
        thesis["entry"].update(thesis_data["entry"])
    if "exit" in thesis_data:
        thesis["exit"].update(thesis_data["exit"])
    if "market_context" in thesis_data:
        thesis["market_context"] = thesis_data["market_context"]
    if "monitoring" in thesis_data:
        thesis["monitoring"].update(thesis_data["monitoring"])
    if "origin" in thesis_data:
        thesis["origin"].update(thesis_data["origin"])

    interval = thesis["monitoring"].get("review_interval_days", DEFAULT_REVIEW_INTERVAL_DAYS)
    base_dt = datetime.fromisoformat(source_base)
    next_review = (base_dt + timedelta(days=interval)).strftime("%Y-%m-%d")
    thesis["monitoring"]["next_review_date"] = next_review

    _validate_thesis(thesis)

    existing_tid = _find_by_fingerprint(state_dir, fingerprint)
    if existing_tid:
        logger.info(
            "Idempotent register: %s already exists for fingerprint %s",
            existing_tid,
            fingerprint[:8],
        )
        return existing_tid

    _save_thesis(state_dir, thesis)
    index = _load_index(state_dir)
    _update_index_entry(index, thesis)
    _save_index(state_dir, index)

    logger.info("Registered thesis %s for %s", thesis_id, thesis["ticker"])
    return thesis_id


def get(state_dir: Path, thesis_id: str) -> dict:
    return _load_thesis(state_dir, thesis_id)


def query(
    state_dir: Path,
    *,
    ticker: str | None = None,
    status: str | None = None,
    thesis_type: str | None = None,
    exchange: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    index = _load_index(state_dir)
    results = []
    for tid, entry in index.get("theses", {}).items():
        if ticker and entry.get("ticker", "").upper() != ticker.upper():
            continue
        if status and entry.get("status") != status:
            continue
        if thesis_type and entry.get("thesis_type") != thesis_type:
            continue
        if exchange and entry.get("exchange") != exchange:
            continue
        created = entry.get("created_at", "")
        if date_from and created < date_from:
            continue
        if date_to and created > date_to:
            continue
        results.append({"thesis_id": tid, **entry})
    return results


def transition(state_dir: Path, thesis_id: str, new_status: str, reason: str) -> dict:
    """IDEA → ENTRY_READY only. ACTIVE/CLOSED/INVALIDATED routed elsewhere."""
    thesis = _load_thesis(state_dir, thesis_id)
    current = thesis["status"]

    if current in _TERMINAL_STATUSES:
        raise ValueError(f"Cannot transition from terminal status {current}")
    if new_status == "ACTIVE":
        raise ValueError("Use open_position() to transition to ACTIVE")
    if new_status in _TERMINAL_STATUSES:
        raise ValueError("Use close() or terminate() to reach a terminal status")

    current_idx = _STATUS_ORDER.index(current)
    try:
        new_idx = _STATUS_ORDER.index(new_status)
    except ValueError:
        raise ValueError(f"Invalid status: {new_status}")
    if new_idx <= current_idx:
        raise ValueError(f"Cannot transition backward from {current} to {new_status}")

    now = _now_iso()
    thesis["status"] = new_status
    thesis["status_history"].append({"status": new_status, "at": now, "reason": reason})
    thesis["updated_at"] = now

    _save_thesis(state_dir, thesis)
    index = _load_index(state_dir)
    _update_index_entry(index, thesis)
    _save_index(state_dir, index)
    return thesis


def attach_position(
    state_dir: Path,
    thesis_id: str,
    position_report_path: str,
    expected_entry: float | None = None,
    expected_stop: float | None = None,
) -> dict:
    """Attach vn-position-sizer output. Enforces lot-100 + VND currency."""
    report_path = Path(position_report_path)
    if not report_path.exists():
        raise FileNotFoundError(f"Position report not found: {position_report_path}")

    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    shares = report.get("final_recommended_shares") or report.get("shares")
    if not shares or shares <= 0:
        raise ValueError("Position report missing positive share count")
    if shares % 100 != 0:
        raise ValueError(f"Lot-100 rule violated: {shares} shares not a multiple of 100")

    params = report.get("parameters", {}) or report.get("inputs", {})
    if expected_entry is not None:
        actual_entry = params.get("entry_price")
        if actual_entry is not None and abs(actual_entry - expected_entry) > 0.01:
            raise ValueError(
                f"Entry mismatch: thesis expects {expected_entry}, report has {actual_entry}"
            )
    if expected_stop is not None:
        actual_stop = params.get("stop_price")
        if actual_stop is not None and abs(actual_stop - expected_stop) > 0.01:
            raise ValueError(
                f"Stop mismatch: thesis expects {expected_stop}, report has {actual_stop}"
            )

    thesis = _load_thesis(state_dir, thesis_id)

    sizing_method = None
    calcs = report.get("calculations", {})
    for method_key in ("fixed_fractional", "atr_based", "kelly"):
        if calcs.get(method_key) is not None:
            sizing_method = calcs[method_key].get("method", method_key)
            break

    position_value = (
        report.get("final_position_value_vnd")
        or report.get("final_position_value")
        or report.get("position_value_vnd")
    )
    risk = report.get("final_risk_vnd") or report.get("final_risk_dollars") or report.get("risk_vnd")

    thesis["position"] = {
        "shares": int(shares),
        "position_value_vnd": float(position_value) if position_value is not None else 0.0,
        "risk_vnd": float(risk) if risk is not None else 0.0,
        "risk_pct_of_account": report.get("final_risk_pct"),
        "account_size_vnd": report.get("account_size_vnd") or params.get("account_size_vnd"),
        "sizing_method": sizing_method,
        "raw_source": {
            "skill": "vn-position-sizer",
            "file": str(position_report_path),
            "fields": {
                "shares": shares,
                "position_value_vnd": position_value,
                "risk_vnd": risk,
            },
        },
    }
    thesis["updated_at"] = _now_iso()

    _save_thesis(state_dir, thesis)
    index = _load_index(state_dir)
    _update_index_entry(index, thesis)
    _save_index(state_dir, index)
    return thesis


def link_report(state_dir: Path, thesis_id: str, skill: str, file: str, date: str) -> dict:
    thesis = _load_thesis(state_dir, thesis_id)
    thesis["linked_reports"].append({"skill": skill, "file": file, "date": date})
    thesis["updated_at"] = _now_iso()
    _save_thesis(state_dir, thesis)
    index = _load_index(state_dir)
    _update_index_entry(index, thesis)
    _save_index(state_dir, index)
    return thesis


def open_position(
    state_dir: Path,
    thesis_id: str,
    actual_price: float,
    actual_date: str,
    reason: str = "lệnh khớp",
    shares: int | None = None,
    event_date: str | None = None,
) -> dict:
    thesis = _load_thesis(state_dir, thesis_id)

    if thesis["status"] != "ENTRY_READY":
        raise ValueError(f"open_position() requires ENTRY_READY status, got {thesis['status']}")
    if shares is not None and shares % 100 != 0:
        raise ValueError(f"Lot-100 rule violated: {shares} shares not a multiple of 100")

    now = _now_iso()
    thesis["entry"]["actual_price"] = actual_price
    thesis["entry"]["actual_date"] = actual_date
    if shares is not None:
        if thesis["position"] is None:
            thesis["position"] = {
                "shares": shares,
                "position_value_vnd": shares * actual_price,
                "risk_vnd": 0.0,
            }
        else:
            thesis["position"]["shares"] = shares

    history_at = event_date or now
    thesis["status"] = "ACTIVE"
    thesis["status_history"].append({"status": "ACTIVE", "at": history_at, "reason": reason})
    thesis["updated_at"] = now

    _save_thesis(state_dir, thesis)
    index = _load_index(state_dir)
    _update_index_entry(index, thesis)
    _save_index(state_dir, index)
    return thesis


def close(
    state_dir: Path,
    thesis_id: str,
    exit_reason: str,
    actual_price: float,
    actual_date: str,
    *,
    broker_fee_pct: float = DEFAULT_BROKER_FEE_PCT,
    sale_tax_pct: float = DEFAULT_SALE_TAX_PCT,
    event_date: str | None = None,
) -> dict:
    """Close an ACTIVE thesis and compute gross + fee + tax + net P&L (VND)."""
    thesis = _load_thesis(state_dir, thesis_id)

    if thesis["status"] != "ACTIVE":
        raise ValueError(f"Can only close ACTIVE thesis, current status: {thesis['status']}")

    entry_price = thesis["entry"].get("actual_price")
    entry_date = thesis["entry"].get("actual_date")
    if entry_price is None:
        raise ValueError("Cannot close: entry.actual_price not set")

    shares = (thesis.get("position") or {}).get("shares") or 0

    thesis["exit"]["actual_price"] = actual_price
    thesis["exit"]["actual_date"] = actual_date
    thesis["exit"]["exit_reason"] = exit_reason

    gross_pnl = (actual_price - entry_price) * shares
    entry_value = entry_price * shares
    exit_value = actual_price * shares
    broker_fee = round(broker_fee_pct * (entry_value + exit_value), 0)
    sale_tax = round(sale_tax_pct * exit_value, 0)
    net_pnl = gross_pnl - broker_fee - sale_tax
    net_pnl_pct = (net_pnl / entry_value * 100) if entry_value else None

    holding_days = None
    if entry_date:
        try:
            holding_days = (_parse_dt(actual_date) - _parse_dt(entry_date)).days
        except (ValueError, TypeError):
            pass

    thesis["outcome"] = {
        "gross_pnl_vnd": round(gross_pnl, 0),
        "broker_fee_vnd": broker_fee,
        "sale_tax_vnd": sale_tax,
        "net_pnl_vnd": round(net_pnl, 0),
        "net_pnl_pct": round(net_pnl_pct, 2) if net_pnl_pct is not None else None,
        "holding_days": holding_days,
        "mae_pct": None,
        "mfe_pct": None,
        "mae_mfe_source": None,
        "lessons_learned": None,
    }

    now = _now_iso()
    history_at = event_date or now
    thesis["status"] = "CLOSED"
    thesis["status_history"].append(
        {"status": "CLOSED", "at": history_at, "reason": f"closed: {exit_reason}"}
    )
    thesis["updated_at"] = now

    _save_thesis(state_dir, thesis)
    index = _load_index(state_dir)
    _update_index_entry(index, thesis)
    _save_index(state_dir, index)

    logger.info("Closed %s: %s, net P&L=%.0f VND", thesis_id, exit_reason, net_pnl)
    return thesis


def terminate(
    state_dir: Path,
    thesis_id: str,
    terminal_status: str,
    exit_reason: str,
    actual_price: float | None = None,
    actual_date: str | None = None,
    event_date: str | None = None,
) -> dict:
    if terminal_status == "CLOSED":
        if actual_price is None or actual_date is None:
            raise ValueError("CLOSED requires actual_price and actual_date")
        return close(
            state_dir, thesis_id, exit_reason, actual_price, actual_date, event_date=event_date
        )

    if terminal_status != "INVALIDATED":
        raise ValueError(f"terminal_status must be CLOSED or INVALIDATED, got {terminal_status}")

    thesis = _load_thesis(state_dir, thesis_id)
    if thesis["status"] in _TERMINAL_STATUSES:
        raise ValueError(f"Already terminal: {thesis['status']}")

    now = _now_iso()
    if actual_price is not None:
        thesis["exit"]["actual_price"] = actual_price
    if actual_date is not None:
        thesis["exit"]["actual_date"] = actual_date
    thesis["exit"]["exit_reason"] = "invalidated"

    entry_price = thesis["entry"].get("actual_price")
    shares = (thesis.get("position") or {}).get("shares") or 0
    if entry_price and actual_price and shares:
        gross_pnl = (actual_price - entry_price) * shares
        entry_value = entry_price * shares
        exit_value = actual_price * shares
        broker_fee = round(DEFAULT_BROKER_FEE_PCT * (entry_value + exit_value), 0)
        sale_tax = round(DEFAULT_SALE_TAX_PCT * exit_value, 0)
        net_pnl = gross_pnl - broker_fee - sale_tax
        thesis["outcome"] = {
            "gross_pnl_vnd": round(gross_pnl, 0),
            "broker_fee_vnd": broker_fee,
            "sale_tax_vnd": sale_tax,
            "net_pnl_vnd": round(net_pnl, 0),
            "net_pnl_pct": round(net_pnl / entry_value * 100, 2) if entry_value else None,
            "holding_days": None,
            "mae_pct": None,
            "mfe_pct": None,
            "mae_mfe_source": None,
            "lessons_learned": None,
        }

    history_at = event_date or now
    thesis["status"] = "INVALIDATED"
    thesis["status_history"].append(
        {"status": "INVALIDATED", "at": history_at, "reason": f"invalidated: {exit_reason}"}
    )
    thesis["updated_at"] = now

    _save_thesis(state_dir, thesis)
    index = _load_index(state_dir)
    _update_index_entry(index, thesis)
    _save_index(state_dir, index)
    return thesis


def mark_reviewed(
    state_dir: Path,
    thesis_id: str,
    *,
    review_date: str,
    outcome: str = "OK",
    notes: str | None = None,
) -> dict:
    valid_outcomes = {"OK", "WARN", "REVIEW"}
    if outcome not in valid_outcomes:
        raise ValueError(f"outcome must be one of {valid_outcomes}, got {outcome}")

    thesis = _load_thesis(state_dir, thesis_id)
    if thesis["status"] in _TERMINAL_STATUSES:
        raise ValueError(f"Cannot review terminal thesis ({thesis['status']})")

    interval = thesis["monitoring"].get("review_interval_days", DEFAULT_REVIEW_INTERVAL_DAYS)
    review_dt = datetime.fromisoformat(f"{review_date}T00:00:00+00:00")
    next_review = (review_dt + timedelta(days=interval)).strftime("%Y-%m-%d")

    thesis["monitoring"]["last_review_date"] = review_date
    thesis["monitoring"]["next_review_date"] = next_review
    thesis["monitoring"]["review_status"] = outcome
    if notes:
        thesis["monitoring"]["alerts"].append(f"[{review_date}] {outcome}: {notes}")
    thesis["updated_at"] = _now_iso()

    _save_thesis(state_dir, thesis)
    index = _load_index(state_dir)
    _update_index_entry(index, thesis)
    _save_index(state_dir, index)
    return thesis


def list_active(state_dir: Path) -> list[dict]:
    return query(state_dir, status="ACTIVE")


def list_review_due(state_dir: Path, as_of: str) -> list[dict]:
    as_of_date = date.fromisoformat(as_of)
    index = _load_index(state_dir)
    results = []
    for tid, entry in index.get("theses", {}).items():
        if entry.get("status") in _TERMINAL_STATUSES:
            continue
        nrd = entry.get("next_review_date")
        if nrd:
            try:
                if date.fromisoformat(nrd) <= as_of_date:
                    results.append({"thesis_id": tid, **entry})
            except ValueError:
                logger.warning("Skipping unparsable next_review_date for %s: %s", tid, nrd)
    return results


def rebuild_index(state_dir: Path) -> dict:
    index = {"version": 1, "theses": {}}
    for yaml_path in sorted(state_dir.glob("th_*.yaml")):
        try:
            thesis = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if thesis and "thesis_id" in thesis:
                _validate_thesis(thesis)
                _update_index_entry(index, thesis)
        except Exception as e:
            logger.warning("Skipping invalid file %s: %s", yaml_path.name, e)
            continue
    _save_index(state_dir, index)
    return index


# -- CLI ----------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="VN Trader Memory — thesis CRUD")
    parser.add_argument("--state-dir", default="state/vn_theses", help="Path to VN thesis state dir")
    sub = parser.add_subparsers(dest="command")

    list_p = sub.add_parser("list", help="List theses")
    list_p.add_argument("--ticker")
    list_p.add_argument("--status")
    list_p.add_argument("--type", dest="thesis_type")
    list_p.add_argument("--exchange", choices=["hose", "hnx", "upcom"])
    list_p.add_argument("--date-from")
    list_p.add_argument("--date-to")

    get_p = sub.add_parser("get", help="Get thesis by ID")
    get_p.add_argument("thesis_id")

    trans_p = sub.add_parser("transition", help="Move thesis status forward")
    trans_p.add_argument("--thesis-id", required=True)
    trans_p.add_argument("--to", required=True, choices=["ENTRY_READY", "ACTIVE"])
    trans_p.add_argument("--reason", default="manual")
    trans_p.add_argument("--actual-entry-price", type=float)
    trans_p.add_argument("--actual-entry-date")
    trans_p.add_argument("--shares", type=int)

    attach_p = sub.add_parser("attach-position", help="Attach vn-position-sizer output")
    attach_p.add_argument("--thesis-id", required=True)
    attach_p.add_argument("--position-sizer-output", required=True)

    close_p = sub.add_parser("close", help="Close an ACTIVE thesis")
    close_p.add_argument("--thesis-id", required=True)
    close_p.add_argument("--exit-price", type=float, required=True)
    close_p.add_argument("--exit-date", required=True)
    close_p.add_argument(
        "--exit-reason",
        default="manual",
        choices=sorted(_VALID_EXIT_REASONS),
    )
    close_p.add_argument("--broker-fee-pct", type=float, default=DEFAULT_BROKER_FEE_PCT)
    close_p.add_argument("--sale-tax-pct", type=float, default=DEFAULT_SALE_TAX_PCT)

    sub.add_parser("rebuild-index", help="Rebuild _index.json from YAML files")

    args = parser.parse_args()
    state_dir = Path(args.state_dir)

    if args.command == "list":
        results = query(
            state_dir,
            ticker=args.ticker,
            status=args.status,
            thesis_type=args.thesis_type,
            exchange=args.exchange,
            date_from=args.date_from,
            date_to=args.date_to,
        )
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif args.command == "get":
        thesis = get(state_dir, args.thesis_id)
        print(yaml.dump(thesis, default_flow_style=False, sort_keys=False, allow_unicode=True))
    elif args.command == "transition":
        if args.to == "ACTIVE":
            if args.actual_entry_price is None or not args.actual_entry_date:
                parser.error("--to ACTIVE requires --actual-entry-price and --actual-entry-date")
            actual_dt = f"{args.actual_entry_date}T00:00:00+00:00"
            t = open_position(
                state_dir,
                args.thesis_id,
                args.actual_entry_price,
                actual_dt,
                reason=args.reason,
                shares=args.shares,
            )
        else:
            t = transition(state_dir, args.thesis_id, args.to, args.reason)
        print(f"Thesis {args.thesis_id} → {t['status']}")
    elif args.command == "attach-position":
        t = attach_position(state_dir, args.thesis_id, args.position_sizer_output)
        print(f"Attached {t['position']['shares']} shares to {args.thesis_id}")
    elif args.command == "close":
        close_dt = f"{args.exit_date}T00:00:00+00:00"
        t = close(
            state_dir,
            args.thesis_id,
            args.exit_reason,
            args.exit_price,
            close_dt,
            broker_fee_pct=args.broker_fee_pct,
            sale_tax_pct=args.sale_tax_pct,
        )
        oc = t["outcome"]
        print(
            f"Closed {args.thesis_id}: net {oc['net_pnl_vnd']:,.0f} VND "
            f"({oc['net_pnl_pct']:+.2f}%)"
        )
    elif args.command == "rebuild-index":
        idx = rebuild_index(state_dir)
        print(f"Rebuilt index: {len(idx['theses'])} theses")
    else:
        parser.print_help()
