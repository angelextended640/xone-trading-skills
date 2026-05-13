"""VN Trader Memory — adapter registry for VN screener outputs.

Each adapter normalises a VN screener's JSON output into a thesis_data dict
that can be passed to vn_thesis_store.register().
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import vn_thesis_store  # noqa: E402

logger = logging.getLogger(__name__)

_ADAPTERS: dict[str, callable] = {}


def _adapter(source_name: str):
    def wrapper(fn):
        _ADAPTERS[source_name] = fn
        return fn

    return wrapper


def _normalize_exchange(value) -> str | None:
    if not value:
        return None
    v = str(value).lower()
    if v in {"hose", "hsx"}:
        return "hose"
    if v == "hnx":
        return "hnx"
    if v == "upcom":
        return "upcom"
    return None


# -- Adapters -----------------------------------------------------------------


@_adapter("vn-vcp-screener")
def ingest_vn_vcp(record: dict, input_file: str) -> dict:
    ticker = record.get("ticker") or record.get("symbol")
    if not ticker:
        raise ValueError("Missing 'ticker'/'symbol' in vn-vcp-screener record")

    thesis_data = {
        "ticker": ticker,
        "exchange": _normalize_exchange(record.get("exchange")),
        "thesis_type": "pivot_breakout",
        "thesis_statement": (
            f"{ticker} VCP breakout — pivot {record.get('pivot_price')}, "
            f"{record.get('contractions', '?')} contractions"
        ),
        "setup_type": "vcp_breakout",
        "_register_reason": "screened by vn-vcp-screener",
        "entry": {},
        "exit": {},
        "origin": {
            "skill": "vn-vcp-screener",
            "output_file": input_file,
            "screening_grade": record.get("grade"),
            "screening_score": record.get("score"),
            "raw_provenance": {k: v for k, v in record.items()},
        },
    }
    if "pivot_price" in record:
        thesis_data["entry"]["target_price"] = record["pivot_price"]
    if "stop_loss" in record:
        thesis_data["exit"]["stop_loss"] = record["stop_loss"]
    return thesis_data


@_adapter("vn-pullback-screener")
def ingest_vn_pullback(record: dict, input_file: str) -> dict:
    ticker = record.get("ticker") or record.get("symbol")
    if not ticker:
        raise ValueError("Missing 'ticker'/'symbol' in vn-pullback-screener record")

    thesis_data = {
        "ticker": ticker,
        "exchange": _normalize_exchange(record.get("exchange")),
        "thesis_type": "mean_reversion",
        "thesis_statement": (
            f"{ticker} pullback — RSI {record.get('rsi', '?')}, "
            f"distance from MA20 {record.get('distance_from_ma20_pct', '?')}%"
        ),
        "setup_type": "ma20_pullback",
        "_register_reason": "screened by vn-pullback-screener",
        "entry": {},
        "exit": {},
        "origin": {
            "skill": "vn-pullback-screener",
            "output_file": input_file,
            "screening_grade": record.get("grade"),
            "screening_score": record.get("score"),
            "raw_provenance": {k: v for k, v in record.items()},
        },
    }
    if "entry_price" in record:
        thesis_data["entry"]["target_price"] = record["entry_price"]
    if "stop_loss" in record:
        thesis_data["exit"]["stop_loss"] = record["stop_loss"]
    return thesis_data


@_adapter("vn-dividend-screener")
def ingest_vn_dividend(record: dict, input_file: str) -> dict:
    ticker = record.get("ticker") or record.get("symbol")
    if not ticker:
        raise ValueError("Missing 'ticker'/'symbol' in vn-dividend-screener record")

    thesis_data = {
        "ticker": ticker,
        "exchange": _normalize_exchange(record.get("exchange")),
        "thesis_type": "dividend_income",
        "thesis_statement": (
            f"{ticker} dividend income — yield {record.get('dividend_yield_pct', '?')}%, "
            f"payout {record.get('payout_ratio', '?')}"
        ),
        "setup_type": "dividend_yield_pullback",
        "_register_reason": "screened by vn-dividend-screener",
        "entry": {},
        "exit": {},
        "origin": {
            "skill": "vn-dividend-screener",
            "output_file": input_file,
            "screening_grade": record.get("grade"),
            "screening_score": record.get("score"),
            "raw_provenance": {k: v for k, v in record.items()},
        },
    }
    if "entry_price" in record:
        thesis_data["entry"]["target_price"] = record["entry_price"]
    if "stop_loss" in record:
        thesis_data["exit"]["stop_loss"] = record["stop_loss"]
    return thesis_data


@_adapter("vn-breakout-trade-planner")
def ingest_vn_breakout(record: dict, input_file: str) -> dict:
    ticker = record.get("ticker") or record.get("symbol")
    if not ticker:
        raise ValueError("Missing 'ticker'/'symbol' in vn-breakout-trade-planner record")

    thesis_data = {
        "ticker": ticker,
        "exchange": _normalize_exchange(record.get("exchange")),
        "thesis_type": "pivot_breakout",
        "thesis_statement": (
            f"{ticker} breakout plan — pivot {record.get('pivot_price', '?')}, "
            f"R-multiple {record.get('r_multiple', '?')}"
        ),
        "setup_type": "breakout_plan",
        "_register_reason": "planned by vn-breakout-trade-planner",
        "entry": {},
        "exit": {},
        "origin": {
            "skill": "vn-breakout-trade-planner",
            "output_file": input_file,
            "screening_grade": record.get("grade"),
            "screening_score": record.get("score"),
            "raw_provenance": {k: v for k, v in record.items()},
        },
    }
    if "entry_price" in record:
        thesis_data["entry"]["target_price"] = record["entry_price"]
    if "stop_loss" in record:
        thesis_data["exit"]["stop_loss"] = record["stop_loss"]
    if "take_profit" in record:
        thesis_data["exit"]["take_profit"] = record["take_profit"]
    if "r_multiple" in record:
        thesis_data["exit"]["take_profit_rr"] = record["r_multiple"]
    return thesis_data


@_adapter("vn-canslim-screener")
def ingest_vn_canslim(record: dict, input_file: str) -> dict:
    ticker = record.get("ticker") or record.get("symbol")
    if not ticker:
        raise ValueError("Missing 'ticker'/'symbol' in vn-canslim-screener record")

    thesis_data = {
        "ticker": ticker,
        "exchange": _normalize_exchange(record.get("exchange")),
        "thesis_type": "growth_momentum",
        "thesis_statement": (
            f"{ticker} CANSLIM — grade {record.get('grade', '?')}, "
            f"score {record.get('score', '?')}/5"
        ),
        "setup_type": "canslim_breakout",
        "_register_reason": "screened by vn-canslim-screener",
        "entry": {},
        "exit": {},
        "origin": {
            "skill": "vn-canslim-screener",
            "output_file": input_file,
            "screening_grade": record.get("grade"),
            "screening_score": record.get("score"),
            "raw_provenance": {k: v for k, v in record.items()},
        },
    }
    return thesis_data


@_adapter("vn-pead-screener")
def ingest_vn_pead(record: dict, input_file: str) -> dict:
    ticker = record.get("ticker") or record.get("symbol")
    if not ticker:
        raise ValueError("Missing 'ticker'/'symbol' in vn-pead-screener record")

    thesis_data = {
        "ticker": ticker,
        "exchange": _normalize_exchange(record.get("exchange")),
        "thesis_type": "earnings_drift",
        "thesis_statement": (
            f"{ticker} PEAD — grade {record.get('grade', '?')}"
        ),
        "setup_type": "pead_pullback",
        "_register_reason": "screened by vn-pead-screener",
        "entry": {},
        "exit": {},
        "origin": {
            "skill": "vn-pead-screener",
            "output_file": input_file,
            "screening_grade": record.get("grade"),
            "raw_provenance": {k: v for k, v in record.items()},
        },
    }
    if "entry_price" in record:
        thesis_data["entry"]["target_price"] = record["entry_price"]
    if "stop_loss" in record:
        thesis_data["exit"]["stop_loss"] = record["stop_loss"]
    if "target_price" in record:
        thesis_data["exit"]["take_profit"] = record["target_price"]
    if "r_multiple" in record:
        thesis_data["exit"]["take_profit_rr"] = record["r_multiple"]
    return thesis_data


# -- Public API ---------------------------------------------------------------


def ingest(source: str, input_file: str, state_dir: str = "state/vn_theses") -> list[str]:
    if source not in _ADAPTERS:
        raise ValueError(f"Unknown source: {source}. Available: {sorted(_ADAPTERS.keys())}")

    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    adapter = _ADAPTERS[source]
    state_path = Path(state_dir)

    source_date = _extract_source_date(data)
    records = _extract_records(data, source)

    thesis_ids = []
    for record in records:
        try:
            thesis_data = adapter(record, input_file)
        except ValueError as e:
            logger.error("Adapter error for %s: %s", source, e)
            continue
        if thesis_data is None:
            continue
        if source_date and "_source_date" not in thesis_data:
            thesis_data["_source_date"] = source_date
        try:
            tid = vn_thesis_store.register(state_path, thesis_data)
            thesis_ids.append(tid)
        except ValueError as e:
            logger.error("Failed to register from %s: %s", source, e)

    return thesis_ids


def _extract_source_date(data: dict | list) -> str | None:
    if isinstance(data, list):
        return None
    for key in ("as_of", "generated_at", "report_date"):
        v = data.get(key)
        if v and isinstance(v, str):
            return v[:10]
    return None


def _extract_records(data: dict | list, source: str) -> list[dict]:
    if isinstance(data, list):
        return data
    for key in ("results", "candidates", "rows", "screened"):
        if key in data and isinstance(data[key], list):
            return data[key]
    if "ticker" in data or "symbol" in data:
        return [data]
    raise ValueError(
        f"Cannot extract records from {source} output. "
        "Expected list, or dict with 'results'/'candidates' key."
    )


def list_adapters() -> list[str]:
    return sorted(_ADAPTERS.keys())


# -- CLI ----------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Ingest VN screener output into vn-trader-memory")
    parser.add_argument("--source", required=True, help=f"One of: {list_adapters()}")
    parser.add_argument("--input", required=True, help="Path to JSON input file")
    parser.add_argument(
        "--state-dir", default="state/vn_theses", help="VN thesis state directory"
    )
    parser.add_argument("--ticker", help="Filter to a single ticker before ingesting")
    args = parser.parse_args()

    if args.ticker:
        # Filter-first: load, filter records, write a temp file, ingest from temp.
        import tempfile

        with open(args.input, encoding="utf-8") as f:
            data = json.load(f)
        records = _extract_records(data, args.source)
        filtered = [
            r
            for r in records
            if (r.get("ticker") or r.get("symbol", "")).upper() == args.ticker.upper()
        ]
        if not filtered:
            logger.error("No records matched ticker %s", args.ticker)
            sys.exit(1)

        # Preserve source_date for fingerprinting
        wrapper = {"results": filtered}
        if isinstance(data, dict):
            for key in ("as_of", "generated_at", "report_date"):
                if key in data:
                    wrapper[key] = data[key]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(wrapper, tmp)
            tmp_path = tmp.name
        try:
            ids = ingest(args.source, tmp_path, args.state_dir)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    else:
        ids = ingest(args.source, args.input, args.state_dir)

    if ids:
        print(f"Registered {len(ids)} thesis(es): {', '.join(ids)}")
    else:
        print("No theses registered.")
        sys.exit(1)
