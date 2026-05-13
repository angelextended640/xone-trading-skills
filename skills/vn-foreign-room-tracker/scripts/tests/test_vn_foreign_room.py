"""Tests for vn-foreign-room-tracker."""

import argparse
import csv
import json
from pathlib import Path

import pytest

from vn_foreign_room import (
    HISTORY_FIELDS,
    append_history,
    classify_status,
    date_n_days_before,
    find_comparison_date,
    find_latest_date,
    load_history,
    parse_input_csv,
    parse_input_json,
    parse_input_row,
    run_history,
    run_record,
    run_report,
)


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------


class TestParseInputRow:
    def test_with_used_and_remaining(self):
        row = parse_input_row(
            {
                "symbol": "vic",
                "room_total": "1869983116",
                "room_used": "1812345678",
                "room_remaining": "57637438",
            },
            "2026-05-13",
        )
        assert row["symbol"] == "VIC"
        assert row["room_total"] == 1869983116
        assert row["room_used"] == 1812345678
        assert row["room_remaining"] == 57637438
        assert row["room_used_pct"] == round(1812345678 / 1869983116 * 100, 4)
        assert row["as_of_date"] == "2026-05-13"

    def test_with_only_used_computes_remaining(self):
        row = parse_input_row(
            {"symbol": "FPT", "room_total": "1000", "room_used": "800"},
            "2026-05-13",
        )
        assert row["room_remaining"] == 200

    def test_with_only_remaining_computes_used(self):
        row = parse_input_row(
            {"symbol": "VNM", "room_total": "1000", "room_remaining": "100"},
            "2026-05-13",
        )
        assert row["room_used"] == 900
        assert row["room_used_pct"] == 90.0

    def test_missing_symbol_raises(self):
        with pytest.raises(ValueError, match="symbol"):
            parse_input_row({"room_total": "1000", "room_used": "500"}, "2026-05-13")

    def test_missing_used_and_remaining_raises(self):
        with pytest.raises(ValueError, match="room_used"):
            parse_input_row({"symbol": "X", "room_total": "1000"}, "2026-05-13")


class TestParseInputCsv:
    def test_csv_roundtrip(self, tmp_path):
        csv_path = tmp_path / "input.csv"
        csv_path.write_text(
            "symbol,room_total,room_used,room_remaining\n"
            "VIC,1000,900,100\n"
            "FPT,500,500,0\n",
            encoding="utf-8",
        )
        rows = parse_input_csv(str(csv_path), "2026-05-13")
        assert len(rows) == 2
        assert rows[0]["symbol"] == "VIC"
        assert rows[1]["room_used_pct"] == 100.0


class TestParseInputJson:
    def test_list_of_records(self, tmp_path):
        path = tmp_path / "input.json"
        path.write_text(
            json.dumps(
                [
                    {"symbol": "VIC", "room_total": 1000, "room_used": 900},
                    {"symbol": "FPT", "room_total": 500, "room_used": 500},
                ]
            ),
            encoding="utf-8",
        )
        rows = parse_input_json(str(path), "2026-05-13")
        assert len(rows) == 2
        assert rows[1]["room_used_pct"] == 100.0

    def test_dict_with_rows(self, tmp_path):
        path = tmp_path / "input.json"
        path.write_text(
            json.dumps(
                {"rows": [{"symbol": "VIC", "room_total": 1000, "room_used": 800}]}
            ),
            encoding="utf-8",
        )
        rows = parse_input_json(str(path), "2026-05-13")
        assert len(rows) == 1


# ---------------------------------------------------------------------------
# History I/O
# ---------------------------------------------------------------------------


class TestHistoryIO:
    def test_append_creates_header(self, tmp_path):
        rows = [
            {
                "as_of_date": "2026-05-13",
                "symbol": "VIC",
                "room_total": 1000,
                "room_used": 900,
                "room_remaining": 100,
                "room_used_pct": 90.0,
            }
        ]
        append_history(tmp_path, rows)
        loaded = load_history(tmp_path)
        assert len(loaded) == 1
        assert loaded[0]["symbol"] == "VIC"

    def test_append_twice_does_not_duplicate_header(self, tmp_path):
        for d in ["2026-05-12", "2026-05-13"]:
            append_history(
                tmp_path,
                [
                    {
                        "as_of_date": d,
                        "symbol": "VIC",
                        "room_total": 1000,
                        "room_used": 900,
                        "room_remaining": 100,
                        "room_used_pct": 90.0,
                    }
                ],
            )
        loaded = load_history(tmp_path)
        assert len(loaded) == 2
        # Make sure no row's symbol cell is "symbol" (would indicate duplicated header)
        for r in loaded:
            assert r["symbol"] == "VIC"


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------


class TestDateHelpers:
    def test_date_n_days_before(self):
        assert date_n_days_before("2026-05-13", 5) == "2026-05-08"
        assert date_n_days_before("2026-05-13", 0) == "2026-05-13"

    def test_find_latest(self):
        history = [
            {"as_of_date": "2026-05-12", "symbol": "VIC"},
            {"as_of_date": "2026-05-13", "symbol": "VIC"},
            {"as_of_date": "2026-05-10", "symbol": "VIC"},
        ]
        assert find_latest_date(history) == "2026-05-13"

    def test_find_latest_empty(self):
        assert find_latest_date([]) is None

    def test_find_comparison_date(self):
        history = [
            {"as_of_date": "2026-05-05", "symbol": "VIC"},
            {"as_of_date": "2026-05-08", "symbol": "VIC"},
            {"as_of_date": "2026-05-13", "symbol": "VIC"},
        ]
        # Looking back 5 days from 2026-05-13 → target = 2026-05-08; that exists
        assert find_comparison_date(history, "2026-05-13", 5) == "2026-05-08"
        # Looking back 7 days → target 2026-05-06; closest ≤ that is 2026-05-05
        assert find_comparison_date(history, "2026-05-13", 7) == "2026-05-05"
        # Looking back 100 days → no candidate
        assert find_comparison_date(history, "2026-05-13", 100) is None


# ---------------------------------------------------------------------------
# Status classification
# ---------------------------------------------------------------------------


class TestClassifyStatus:
    @pytest.fixture
    def cfg(self):
        return dict(full_threshold=99.0, release_threshold=90.0, spike_threshold=5.0)

    def test_normal_no_prior(self, cfg):
        row = {"symbol": "X", "room_used_pct": 50.0, "room_remaining": 500}
        status, msg = classify_status(row, None, **cfg)
        assert status == "normal"
        assert msg is None

    def test_full_no_prior(self, cfg):
        row = {"symbol": "X", "room_used_pct": 99.5, "room_remaining": 50}
        status, msg = classify_status(row, None, **cfg)
        assert status == "full"
        # No prior → no transition alert
        assert msg is None

    def test_high_usage(self, cfg):
        row = {"symbol": "X", "room_used_pct": 95.0, "room_remaining": 500}
        status, msg = classify_status(row, None, **cfg)
        assert status == "high_usage"
        assert msg is None

    def test_just_became_full(self, cfg):
        row = {"symbol": "X", "room_used_pct": 99.5, "room_remaining": 50}
        prior = {"symbol": "X", "room_used_pct": 95.0, "room_remaining": 500}
        status, msg = classify_status(row, prior, **cfg)
        assert status == "full"
        assert msg is not None
        assert "đầy room" in msg

    def test_released_from_full(self, cfg):
        row = {"symbol": "X", "room_used_pct": 85.0, "room_remaining": 1500}
        prior = {"symbol": "X", "room_used_pct": 99.5, "room_remaining": 50}
        status, msg = classify_status(row, prior, **cfg)
        assert status == "released"
        assert msg is not None
        assert "giải phóng" in msg

    def test_spike_up(self, cfg):
        row = {"symbol": "X", "room_used_pct": 85.0, "room_remaining": 1500}
        prior = {"symbol": "X", "room_used_pct": 70.0, "room_remaining": 3000}
        status, msg = classify_status(row, prior, **cfg)
        assert status == "spike_up"
        assert msg is not None
        assert "tăng" in msg

    def test_spike_down_but_not_released(self, cfg):
        # Was high_usage, dropped sharply but still above release_threshold? No —
        # 95 → 85 = -10 → still spike_down because not coming from full
        row = {"symbol": "X", "room_used_pct": 85.0, "room_remaining": 1500}
        prior = {"symbol": "X", "room_used_pct": 95.0, "room_remaining": 500}
        status, msg = classify_status(row, prior, **cfg)
        assert status == "spike_down"

    def test_no_spike_under_threshold(self, cfg):
        row = {"symbol": "X", "room_used_pct": 73.0, "room_remaining": 2700}
        prior = {"symbol": "X", "room_used_pct": 70.0, "room_remaining": 3000}
        status, msg = classify_status(row, prior, **cfg)
        assert status == "normal"
        assert msg is None


# ---------------------------------------------------------------------------
# End-to-end subcommands
# ---------------------------------------------------------------------------


def make_args(**kwargs):
    defaults = dict(
        as_of=None,
        lookback_days=5,
        full_threshold=99.0,
        release_threshold=90.0,
        spike_threshold=5.0,
        days=30,
        input=None,
        symbol=None,
        output_dir="/tmp/test",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestRunRecord:
    def test_record_csv(self, tmp_path):
        # Build input CSV
        in_csv = tmp_path / "input.csv"
        in_csv.write_text(
            "symbol,room_total,room_used,room_remaining\n"
            "VIC,1000,900,100\n"
            "FPT,500,500,0\n",
            encoding="utf-8",
        )
        result = run_record(
            make_args(
                input=str(in_csv),
                as_of="2026-05-13",
                state_dir=str(tmp_path),
            )
        )
        assert result["rows_ingested"] == 2
        assert "VIC" in result["symbols"]
        assert "FPT" in result["symbols"]
        # Verify history persisted
        history = load_history(tmp_path)
        assert len(history) == 2


class TestRunReport:
    def test_report_with_alerts(self, tmp_path):
        # Seed history: FPT was full 2026-05-08, now 85% — released
        # VIC normal both days
        rows = [
            # 2026-05-08
            {
                "as_of_date": "2026-05-08",
                "symbol": "FPT",
                "room_total": 1000,
                "room_used": 999,
                "room_remaining": 1,
                "room_used_pct": 99.9,
            },
            {
                "as_of_date": "2026-05-08",
                "symbol": "VIC",
                "room_total": 1000,
                "room_used": 500,
                "room_remaining": 500,
                "room_used_pct": 50.0,
            },
            # 2026-05-13
            {
                "as_of_date": "2026-05-13",
                "symbol": "FPT",
                "room_total": 1000,
                "room_used": 850,
                "room_remaining": 150,
                "room_used_pct": 85.0,
            },
            {
                "as_of_date": "2026-05-13",
                "symbol": "VIC",
                "room_total": 1000,
                "room_used": 510,
                "room_remaining": 490,
                "room_used_pct": 51.0,
            },
        ]
        append_history(tmp_path, rows)

        result = run_report(
            make_args(
                state_dir=str(tmp_path),
                lookback_days=5,
                full_threshold=99.0,
                release_threshold=90.0,
                spike_threshold=5.0,
            )
        )
        assert result["latest_date"] == "2026-05-13"
        assert result["comparison_date"] == "2026-05-08"

        # FPT should be flagged as released
        fpt_row = next(r for r in result["rows"] if r["symbol"] == "FPT")
        assert fpt_row["status"] == "released"

        # VIC should be normal
        vic_row = next(r for r in result["rows"] if r["symbol"] == "VIC")
        assert vic_row["status"] == "normal"

        # Alerts should contain FPT released
        alert_msgs = [a["msg"] for a in result["alerts"]]
        assert any("FPT" in m and "giải phóng" in m for m in alert_msgs)

    def test_report_empty_history_raises(self, tmp_path):
        with pytest.raises(ValueError, match="history"):
            run_report(
                make_args(
                    state_dir=str(tmp_path),
                    lookback_days=5,
                    full_threshold=99.0,
                    release_threshold=90.0,
                    spike_threshold=5.0,
                )
            )


class TestRunHistory:
    def test_history_filters_by_symbol(self, tmp_path):
        rows = [
            {
                "as_of_date": "2026-05-13",
                "symbol": "VIC",
                "room_total": 1000,
                "room_used": 500,
                "room_remaining": 500,
                "room_used_pct": 50.0,
            },
            {
                "as_of_date": "2026-05-13",
                "symbol": "FPT",
                "room_total": 1000,
                "room_used": 999,
                "room_remaining": 1,
                "room_used_pct": 99.9,
            },
        ]
        append_history(tmp_path, rows)
        result = run_history(
            make_args(symbol="VIC", state_dir=str(tmp_path), days=30)
        )
        assert result["symbol"] == "VIC"
        assert result["row_count"] == 1
        assert result["rows"][0]["symbol"] == "VIC"

    def test_history_respects_days_filter(self, tmp_path):
        # 10 days of VIC data
        rows = []
        for i in range(10):
            d = f"2026-05-{i+4:02d}"  # 04 to 13
            rows.append(
                {
                    "as_of_date": d,
                    "symbol": "VIC",
                    "room_total": 1000,
                    "room_used": 500 + i,
                    "room_remaining": 500 - i,
                    "room_used_pct": 50.0 + i * 0.1,
                }
            )
        append_history(tmp_path, rows)

        result = run_history(
            make_args(symbol="VIC", state_dir=str(tmp_path), days=3)
        )
        # Latest is 2026-05-13; 3 days back = 2026-05-10 → 4 rows (10, 11, 12, 13)
        assert result["row_count"] == 4
