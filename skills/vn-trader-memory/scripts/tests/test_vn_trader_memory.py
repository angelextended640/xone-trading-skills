"""Tests for vn-trader-memory: store, ingest, review, postmortem.

All tests are offline — vnstock is never called. MAE/MFE coverage uses
the in-process FixtureAdapter from vn_price_adapter.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

import vn_thesis_ingest
import vn_thesis_review
import vn_thesis_store
from vn_price_adapter import FixtureAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_thesis_data(**overrides):
    base = {
        "ticker": "FPT",
        "exchange": "hose",
        "thesis_type": "pivot_breakout",
        "thesis_statement": "FPT VCP breakout setup",
        "_register_reason": "unit test",
        "origin": {
            "skill": "vn-vcp-screener",
            "output_file": "reports/test.json",
            "screening_grade": "A",
            "screening_score": 88,
            "raw_provenance": {"contractions": 3},
        },
    }
    base.update(overrides)
    return base


def _write_position_report(path: Path, *, shares: int, entry: float, stop: float) -> Path:
    payload = {
        "mode": "shares",
        "parameters": {"entry_price": entry, "stop_price": stop},
        "final_recommended_shares": shares,
        "final_position_value_vnd": shares * entry,
        "final_risk_vnd": shares * max(0.0, entry - stop),
        "final_risk_pct": 0.5,
        "calculations": {
            "fixed_fractional": {"method": "fixed_fractional"},
            "atr_based": None,
            "kelly": None,
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Store: register / get / query / transitions
# ---------------------------------------------------------------------------


def test_register_creates_yaml_and_index(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    tid = vn_thesis_store.register(state_dir, _minimal_thesis_data())

    assert tid.startswith("th_fpt_pvt_")
    yaml_path = state_dir / f"{tid}.yaml"
    assert yaml_path.exists()

    idx = json.loads((state_dir / "_index.json").read_text(encoding="utf-8"))
    assert tid in idx["theses"]
    entry = idx["theses"][tid]
    assert entry["ticker"] == "FPT"
    assert entry["exchange"] == "hose"
    assert entry["status"] == "IDEA"


def test_register_is_idempotent_on_fingerprint(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    data = _minimal_thesis_data(_source_date="2026-05-13")
    first = vn_thesis_store.register(state_dir, data)
    second = vn_thesis_store.register(state_dir, dict(data))
    assert first == second


def test_register_rejects_unknown_thesis_type(tmp_path: Path):
    with pytest.raises(ValueError, match="Invalid thesis_type"):
        vn_thesis_store.register(
            tmp_path / "vn_theses", _minimal_thesis_data(thesis_type="bogus")
        )


def test_register_default_review_interval_is_five_days(tmp_path: Path):
    """Phase A3 plan: review_interval_days default is 5 (not 30)."""
    state_dir = tmp_path / "vn_theses"
    tid = vn_thesis_store.register(
        state_dir, _minimal_thesis_data(_source_date="2026-05-13")
    )
    thesis = vn_thesis_store.get(state_dir, tid)
    assert thesis["monitoring"]["review_interval_days"] == 5
    assert thesis["monitoring"]["next_review_date"] == "2026-05-18"


def test_register_with_source_date_uses_report_date_for_id(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    tid = vn_thesis_store.register(
        state_dir, _minimal_thesis_data(_source_date="2026-05-13")
    )
    assert "20260513" in tid


def test_transition_idea_to_entry_ready(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    tid = vn_thesis_store.register(state_dir, _minimal_thesis_data())
    thesis = vn_thesis_store.transition(state_dir, tid, "ENTRY_READY", "size confirmed")
    assert thesis["status"] == "ENTRY_READY"
    assert thesis["status_history"][-1]["status"] == "ENTRY_READY"


def test_transition_blocks_skipping_to_active(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    tid = vn_thesis_store.register(state_dir, _minimal_thesis_data())
    with pytest.raises(ValueError, match="open_position"):
        vn_thesis_store.transition(state_dir, tid, "ACTIVE", "skip")


def test_transition_blocks_backward(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    tid = vn_thesis_store.register(state_dir, _minimal_thesis_data())
    vn_thesis_store.transition(state_dir, tid, "ENTRY_READY", "ok")
    with pytest.raises(ValueError, match="backward"):
        vn_thesis_store.transition(state_dir, tid, "IDEA", "rewind")


# ---------------------------------------------------------------------------
# Lot-100 validation
# ---------------------------------------------------------------------------


def test_attach_position_rejects_non_lot_100(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    tid = vn_thesis_store.register(state_dir, _minimal_thesis_data())
    bad_report = _write_position_report(
        tmp_path / "bad.json", shares=137, entry=142000, stop=135000
    )
    with pytest.raises(ValueError, match="Lot-100"):
        vn_thesis_store.attach_position(state_dir, tid, str(bad_report))


def test_attach_position_accepts_lot_100(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    tid = vn_thesis_store.register(state_dir, _minimal_thesis_data())
    report = _write_position_report(
        tmp_path / "ok.json", shares=700, entry=142000, stop=135000
    )
    thesis = vn_thesis_store.attach_position(state_dir, tid, str(report))
    assert thesis["position"]["shares"] == 700
    assert thesis["position"]["position_value_vnd"] == 700 * 142000


def test_open_position_rejects_non_lot_100(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    tid = vn_thesis_store.register(state_dir, _minimal_thesis_data())
    vn_thesis_store.transition(state_dir, tid, "ENTRY_READY", "ok")
    with pytest.raises(ValueError, match="Lot-100"):
        vn_thesis_store.open_position(
            state_dir, tid, 142000, "2026-05-13T09:00:00+07:00", shares=350
        )


# ---------------------------------------------------------------------------
# Close + VND P&L accounting
# ---------------------------------------------------------------------------


def _build_active_thesis(state_dir: Path, *, shares: int = 700, entry: float = 142000) -> str:
    tid = vn_thesis_store.register(state_dir, _minimal_thesis_data())
    vn_thesis_store.transition(state_dir, tid, "ENTRY_READY", "ok")
    report = _write_position_report(
        state_dir.parent / "pos.json", shares=shares, entry=entry, stop=entry * 0.95
    )
    vn_thesis_store.attach_position(state_dir, tid, str(report))
    vn_thesis_store.open_position(
        state_dir, tid, entry, "2026-05-13T09:00:00+07:00", shares=shares
    )
    return tid


def test_close_computes_gross_fee_tax_net(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    tid = _build_active_thesis(state_dir, shares=700, entry=142000)

    thesis = vn_thesis_store.close(
        state_dir, tid, "target_hit", 152000, "2026-06-04T15:00:00+07:00"
    )

    o = thesis["outcome"]
    # Gross: (152000 - 142000) * 700 = 7,000,000
    assert o["gross_pnl_vnd"] == 7_000_000
    # Broker fee: 0.0015 * (700*142000 + 700*152000) = 0.0015 * 205_800_000 = 308,700
    assert o["broker_fee_vnd"] == 308_700
    # Sale tax: 0.001 * 700 * 152000 = 106,400
    assert o["sale_tax_vnd"] == 106_400
    # Net: 7,000,000 - 308,700 - 106,400 = 6,584,900
    assert o["net_pnl_vnd"] == 6_584_900
    # Net %: 6,584,900 / (700*142000) * 100 ≈ 6.62
    assert o["net_pnl_pct"] == pytest.approx(6.62, abs=0.05)


def test_close_uses_custom_broker_fee(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    tid = _build_active_thesis(state_dir, shares=700, entry=142000)
    thesis = vn_thesis_store.close(
        state_dir,
        tid,
        "manual",
        152000,
        "2026-06-04T15:00:00+07:00",
        broker_fee_pct=0.001,  # 0.10% (private-banking tier)
    )
    # 0.001 * 205,800,000 = 205,800
    assert thesis["outcome"]["broker_fee_vnd"] == 205_800


def test_close_blocks_non_active(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    tid = vn_thesis_store.register(state_dir, _minimal_thesis_data())
    with pytest.raises(ValueError, match="Can only close ACTIVE"):
        vn_thesis_store.close(state_dir, tid, "manual", 150000, "2026-06-04T00:00:00+07:00")


# ---------------------------------------------------------------------------
# Review + summary
# ---------------------------------------------------------------------------


def test_list_review_due(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    vn_thesis_store.register(state_dir, _minimal_thesis_data(_source_date="2026-05-01"))
    # next_review = 2026-05-06; "today" = 2026-05-18 → due
    due = vn_thesis_store.list_review_due(state_dir, "2026-05-18")
    assert len(due) == 1


def test_mark_reviewed_advances_next_date(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    tid = vn_thesis_store.register(state_dir, _minimal_thesis_data())
    thesis = vn_thesis_store.mark_reviewed(
        state_dir, tid, review_date="2026-05-20", outcome="OK", notes="held above MA20"
    )
    assert thesis["monitoring"]["last_review_date"] == "2026-05-20"
    assert thesis["monitoring"]["next_review_date"] == "2026-05-25"
    assert "held above MA20" in thesis["monitoring"]["alerts"][0]


def test_summary_stats_includes_net_pnl_pct(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    tid = _build_active_thesis(state_dir, shares=700, entry=142000)
    vn_thesis_store.close(state_dir, tid, "target_hit", 152000, "2026-06-04T15:00:00+07:00")
    stats = vn_thesis_review.summary_stats(str(state_dir))
    assert stats["count"] == 1
    assert stats["win_rate"] == 1.0
    assert stats["avg_net_pnl_pct"] > 0


# ---------------------------------------------------------------------------
# Ingest adapters
# ---------------------------------------------------------------------------


def _write_screener_output(path: Path, source: str, ticker: str = "FPT") -> Path:
    if source == "vn-vcp-screener":
        record = {
            "ticker": ticker,
            "exchange": "HOSE",
            "pivot_price": 142000,
            "stop_loss": 135000,
            "contractions": 3,
            "grade": "A",
            "score": 88,
        }
    elif source == "vn-pullback-screener":
        record = {
            "ticker": ticker,
            "exchange": "hose",
            "entry_price": 50000,
            "stop_loss": 47500,
            "rsi": 38.5,
            "distance_from_ma20_pct": -2.1,
            "grade": "B",
            "score": 70,
        }
    elif source == "vn-dividend-screener":
        record = {
            "ticker": ticker,
            "exchange": "hose",
            "entry_price": 75000,
            "stop_loss": 71000,
            "dividend_yield_pct": 8.5,
            "payout_ratio": 60,
            "grade": "A",
            "score": 82,
        }
    elif source == "vn-breakout-trade-planner":
        record = {
            "ticker": ticker,
            "exchange": "HOSE",
            "entry_price": 120000,
            "stop_loss": 114000,
            "take_profit": 132000,
            "r_multiple": 2.0,
            "grade": "A",
            "score": 85,
        }
    else:
        raise ValueError(source)

    payload = {"as_of": "2026-05-13", "results": [record]}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "source,expected_type",
    [
        ("vn-vcp-screener", "pivot_breakout"),
        ("vn-pullback-screener", "mean_reversion"),
        ("vn-dividend-screener", "dividend_income"),
        ("vn-breakout-trade-planner", "pivot_breakout"),
    ],
)
def test_ingest_each_adapter_registers_thesis(tmp_path: Path, source, expected_type):
    state_dir = tmp_path / "vn_theses"
    input_path = _write_screener_output(tmp_path / "in.json", source, ticker="FPT")
    ids = vn_thesis_ingest.ingest(source, str(input_path), str(state_dir))
    assert len(ids) == 1
    thesis = vn_thesis_store.get(state_dir, ids[0])
    assert thesis["thesis_type"] == expected_type
    assert thesis["ticker"] == "FPT"
    assert thesis["exchange"] == "hose"
    assert thesis["origin"]["skill"] == source
    assert thesis["origin"]["screening_grade"] in {"A", "B"}


def test_ingest_unknown_source_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="Unknown source"):
        vn_thesis_ingest.ingest("not-a-real-source", str(tmp_path), str(tmp_path))


def test_ingest_preserves_source_date(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    input_path = _write_screener_output(tmp_path / "in.json", "vn-vcp-screener")
    ids = vn_thesis_ingest.ingest("vn-vcp-screener", str(input_path), str(state_dir))
    thesis = vn_thesis_store.get(state_dir, ids[0])
    assert thesis["created_at"].startswith("2026-05-13")


# ---------------------------------------------------------------------------
# Postmortem + MAE/MFE with FixtureAdapter
# ---------------------------------------------------------------------------


def test_postmortem_with_fixture_prices(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    journal_dir = tmp_path / "vn_journal"
    tid = _build_active_thesis(state_dir, shares=700, entry=142000)
    vn_thesis_store.close(state_dir, tid, "target_hit", 152000, "2026-06-04T15:00:00+07:00")

    # Build a synthetic daily-close series. Skip T+0/T+1 in adapter.
    series = {
        "FPT": [
            {"date": "2026-05-13", "close": 142000},  # T+0 (skipped)
            {"date": "2026-05-14", "close": 141000},  # T+1 (skipped)
            {"date": "2026-05-15", "close": 139000},  # MAE base candidate
            {"date": "2026-05-20", "close": 145000},
            {"date": "2026-05-28", "close": 154000},  # MFE
            {"date": "2026-06-04", "close": 152000},
        ]
    }
    adapter = FixtureAdapter(series)
    pm_path = vn_thesis_review.generate_postmortem(
        tid, str(state_dir), price_adapter=adapter, journal_dir=str(journal_dir)
    )

    assert Path(pm_path).exists()
    content = Path(pm_path).read_text(encoding="utf-8")
    assert "Postmortem" in content
    assert "Net P&L" in content

    # MAE = (139000 - 142000) / 142000 * 100 ≈ -2.11%
    # MFE = (154000 - 142000) / 142000 * 100 ≈ +8.45%
    thesis = vn_thesis_store.get(state_dir, tid)
    assert thesis["outcome"]["mae_pct"] == pytest.approx(-2.11, abs=0.05)
    assert thesis["outcome"]["mfe_pct"] == pytest.approx(8.45, abs=0.05)
    assert thesis["outcome"]["mae_mfe_source"] == "vnstock"


def test_postmortem_without_prices_marks_manual(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    journal_dir = tmp_path / "vn_journal"
    tid = _build_active_thesis(state_dir, shares=700, entry=142000)
    vn_thesis_store.close(state_dir, tid, "target_hit", 152000, "2026-06-04T15:00:00+07:00")

    pm_path = vn_thesis_review.generate_postmortem(
        tid, str(state_dir), price_adapter=None, journal_dir=str(journal_dir)
    )

    thesis = vn_thesis_store.get(state_dir, tid)
    assert thesis["outcome"]["mae_pct"] is None
    assert thesis["outcome"]["mfe_pct"] is None
    assert thesis["outcome"]["mae_mfe_source"] == "manual"
    assert Path(pm_path).exists()


def test_postmortem_skips_first_two_sessions():
    """T+0/T+1 must be excluded from MAE/MFE — shares not yet liquidatable."""
    series = {
        "FPT": [
            {"date": "2026-05-13", "close": 100000},  # would be MFE if included
            {"date": "2026-05-14", "close": 130000},  # would be MFE if included
            {"date": "2026-05-15", "close": 105000},
            {"date": "2026-05-16", "close": 110000},
        ]
    }
    adapter = FixtureAdapter(series, skip_sessions=2)
    closes = adapter.get_daily_closes("FPT", "2026-05-13", "2026-05-20")
    assert all(row["date"] >= "2026-05-15" for row in closes)


# ---------------------------------------------------------------------------
# Rebuild index recovery
# ---------------------------------------------------------------------------


def test_rebuild_index_from_yaml_files(tmp_path: Path):
    state_dir = tmp_path / "vn_theses"
    tid = vn_thesis_store.register(state_dir, _minimal_thesis_data())
    # Corrupt the index
    (state_dir / "_index.json").write_text('{"version": 1, "theses": {}}', encoding="utf-8")
    rebuilt = vn_thesis_store.rebuild_index(state_dir)
    assert tid in rebuilt["theses"]
