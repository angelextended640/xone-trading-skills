"""Tests for vn-margin-rules-monitor."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import vn_margin_monitor as mod


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _seed_broker_csv(tmp_path: Path, broker: str, rows: str) -> Path:
    """Write a broker margin CSV and return its path."""
    p = tmp_path / f"{broker.lower()}_input.csv"
    p.write_text(rows, encoding="utf-8")
    return p


# -----------------------------------------------------------------------------
# is_q_rated
# -----------------------------------------------------------------------------


def test_is_q_rated_recognises_common_phrases():
    assert mod.is_q_rated("Q-rated")
    assert mod.is_q_rated("Kiểm soát")
    assert mod.is_q_rated("Hạn chế")
    assert mod.is_q_rated("Tạm ngừng")
    assert mod.is_q_rated("Suspended margin")
    assert mod.is_q_rated("warning issued")


def test_is_q_rated_returns_false_for_clean_note():
    assert mod.is_q_rated("") is False
    assert mod.is_q_rated("normal") is False
    assert mod.is_q_rated(None) is False  # tolerant of None


# -----------------------------------------------------------------------------
# record_margin
# -----------------------------------------------------------------------------


def test_record_margin_writes_latest_and_history(tmp_path):
    state = tmp_path / "state"
    csv_file = _seed_broker_csv(tmp_path, "TCBS", "symbol,rate,note\nFPT,50,\nVIC,30,Q-rated\n")
    ok = mod.record_margin("TCBS", str(csv_file), str(state))
    assert ok
    latest = state / "tcbs_margin_list.csv"
    assert latest.exists()
    assert "FPT,50" in latest.read_text(encoding="utf-8")
    # history copy exists
    hist_files = list((state / "history").glob("tcbs_*.csv"))
    assert len(hist_files) == 1
    assert "FPT,50" in hist_files[0].read_text(encoding="utf-8")


def test_record_margin_missing_input_returns_false(tmp_path, capsys):
    state = tmp_path / "state"
    ok = mod.record_margin("TCBS", str(tmp_path / "missing.csv"), str(state))
    assert ok is False
    err = capsys.readouterr().err
    assert "không tìm thấy" in err


# -----------------------------------------------------------------------------
# check_symbol
# -----------------------------------------------------------------------------


def test_check_symbol_finds_single_broker(tmp_path):
    state = tmp_path / "state"
    csv_file = _seed_broker_csv(tmp_path, "TCBS", "symbol,rate,note\nFPT,50,\n")
    mod.record_margin("TCBS", str(csv_file), str(state))
    res = mod.check_symbol("FPT", str(state))
    assert "TCBS" in res
    assert res["TCBS"]["rate"] == "50"


def test_check_symbol_aggregates_multiple_brokers(tmp_path):
    state = tmp_path / "state"
    mod.record_margin(
        "TCBS",
        str(_seed_broker_csv(tmp_path, "TCBS_in", "symbol,rate,note\nFPT,50,\n")),
        str(state),
    )
    mod.record_margin(
        "SSI",
        str(_seed_broker_csv(tmp_path, "SSI_in", "symbol,rate,note\nFPT,40,\n")),
        str(state),
    )
    res = mod.check_symbol("FPT", str(state))
    assert set(res.keys()) == {"TCBS", "SSI"}
    assert res["TCBS"]["rate"] == "50"
    assert res["SSI"]["rate"] == "40"


def test_check_symbol_case_insensitive(tmp_path):
    state = tmp_path / "state"
    mod.record_margin(
        "TCBS",
        str(_seed_broker_csv(tmp_path, "in", "symbol,rate,note\nfpt,50,\n")),
        str(state),
    )
    res = mod.check_symbol("FPT", str(state))
    assert "TCBS" in res


def test_check_symbol_not_found_returns_empty(tmp_path):
    state = tmp_path / "state"
    mod.record_margin(
        "TCBS",
        str(_seed_broker_csv(tmp_path, "in", "symbol,rate,note\nFPT,50,\n")),
        str(state),
    )
    res = mod.check_symbol("UNKNOWN", str(state))
    assert res == {}


# -----------------------------------------------------------------------------
# report_brokers
# -----------------------------------------------------------------------------


def test_report_brokers_counts_q_rated_and_zero_rate(tmp_path):
    state = tmp_path / "state"
    mod.record_margin(
        "TCBS",
        str(
            _seed_broker_csv(
                tmp_path,
                "in",
                "symbol,rate,note\nFPT,50,\nVIC,30,Q-rated\nHPG,0,Suspended margin\n",
            )
        ),
        str(state),
    )
    payload = mod.report_brokers(str(state))
    assert payload["broker_count"] == 1
    row = payload["brokers"][0]
    assert row["broker"] == "TCBS"
    assert row["total_symbols"] == 3
    assert row["zero_rate_count"] == 1
    assert row["q_rated_count"] == 2  # VIC (Q-rated) + HPG (Suspended)
    assert "VIC" in row["q_rated_symbols"]


def test_report_brokers_empty_state_returns_zero(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    payload = mod.report_brokers(str(state))
    assert payload["broker_count"] == 0
    assert payload["brokers"] == []


# -----------------------------------------------------------------------------
# list_history
# -----------------------------------------------------------------------------


def test_list_history_records_snapshots(tmp_path):
    state = tmp_path / "state"
    mod.record_margin(
        "TCBS",
        str(_seed_broker_csv(tmp_path, "in", "symbol,rate,note\nFPT,50,\nVIC,40,\n")),
        str(state),
    )
    payload = mod.list_history("TCBS", str(state))
    assert payload["snapshot_count"] >= 1
    assert payload["broker"] == "TCBS"
    assert payload["snapshots"][0]["row_count"] == 2


def test_list_history_unknown_broker_returns_empty(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    payload = mod.list_history("UNKNOWN", str(state))
    assert payload["snapshot_count"] == 0
    assert payload["snapshots"] == []
