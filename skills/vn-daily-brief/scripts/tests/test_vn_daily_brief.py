"""Tests for vn-daily-brief orchestrator."""

import argparse
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

import vn_daily_brief as mod


def _make_args(**overrides) -> argparse.Namespace:
    defaults = dict(
        ohlcv_glob="reports/vn_ohlcv_*.json",
        room_state_dir="state/vn_foreign_room",
        portfolio_state_dir="state/vn_portfolio",
        prices="",
        account_size="1000000000",
        lookback_days=1,
        output_dir="reports/",
        strict=False,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


@patch("vn_daily_brief.subprocess.run")
def test_run_command_success(mock_run):
    """run_command returns (True, stdout) on rc=0."""
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
    ok, body = mod.run_command(["echo", "ok"])
    assert ok is True
    assert body == "ok"


@patch("vn_daily_brief.subprocess.run")
def test_run_command_failure_falls_back_to_stderr(mock_run):
    """run_command returns (False, stderr) on non-zero rc."""
    mock_run.return_value = MagicMock(returncode=2, stdout="", stderr="boom")
    ok, body = mod.run_command(["false"])
    assert ok is False
    assert "boom" in body


@patch("vn_daily_brief.subprocess.run")
def test_run_command_file_not_found(mock_run):
    """run_command surfaces FileNotFoundError as a failure, not an exception."""
    mock_run.side_effect = FileNotFoundError("no such binary")
    ok, body = mod.run_command(["nonexistent"])
    assert ok is False
    assert "not found" in body.lower()


@patch("vn_daily_brief.subprocess.run")
def test_run_command_accepts_string(mock_run):
    """run_command splits a string command via shlex."""
    mock_run.return_value = MagicMock(returncode=0, stdout="hello", stderr="")
    ok, body = mod.run_command("echo hello")
    assert ok is True
    args_called, _ = mock_run.call_args
    assert args_called[0] == ["echo", "hello"]


@patch("vn_daily_brief.run_command")
def test_assemble_brief_all_ok(mock_rc):
    """assemble_brief aggregates 3 sub-skills correctly when all succeed."""
    mock_rc.return_value = (True, "section body")
    brief = mod.assemble_brief(_make_args())
    assert brief["all_ok"] is True
    assert len(brief["sections"]) == 3
    assert all(s["ok"] for s in brief["sections"])
    assert brief["failures"] == []


@patch("vn_daily_brief.run_command")
def test_assemble_brief_records_failures(mock_rc):
    """assemble_brief marks all_ok=False and lists failed sections."""
    mock_rc.side_effect = [(True, "ok"), (False, "boom"), (True, "ok")]
    brief = mod.assemble_brief(_make_args())
    assert brief["all_ok"] is False
    assert len(brief["failures"]) == 1
    assert "Room ngoại" in brief["failures"][0]["title"]


def test_render_markdown_contains_headers_and_status_icons():
    brief = {
        "as_of": "2026-05-13",
        "timestamp": "2026-05-13_07:30:00",
        "sections": [
            {"title": "1. A", "ok": True, "body": "good"},
            {"title": "2. B", "ok": False, "body": "fail"},
        ],
        "failures": [{"title": "2. B"}],
        "all_ok": False,
    }
    md = mod.render_markdown(brief)
    assert "# VN Daily Brief — 2026-05-13" in md
    assert "Asia/Ho_Chi_Minh" in md
    assert "✅ 1. A" in md
    assert "⚠️ 2. B" in md
    assert "1 sub-skill" in md  # warning banner


def test_write_report_creates_file(tmp_path):
    brief = {
        "as_of": "2026-05-13",
        "timestamp": "2026-05-13_07:30:00",
        "sections": [{"title": "1. X", "ok": True, "body": "hi"}],
        "failures": [],
        "all_ok": True,
    }
    out = mod.write_report(brief, str(tmp_path))
    assert out.exists()
    assert out.name == "vn_daily_brief_2026-05-13.md"
    text = out.read_text(encoding="utf-8")
    assert "1. X" in text


@patch("vn_daily_brief.run_command")
def test_main_strict_mode_exits_nonzero_on_failure(mock_rc, tmp_path, monkeypatch):
    """--strict + at least one sub-skill failure → exit 1."""
    mock_rc.return_value = (False, "boom")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "vn_daily_brief.py",
            "--strict",
            "--output-dir",
            str(tmp_path),
        ],
    )
    rc = mod.main()
    assert rc == 1


@patch("vn_daily_brief.run_command")
def test_main_default_mode_returns_zero_even_on_failure(mock_rc, tmp_path, monkeypatch):
    """Default mode tolerates failures (returns 0) so the brief still produces a file."""
    mock_rc.return_value = (False, "boom")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "vn_daily_brief.py",
            "--output-dir",
            str(tmp_path),
        ],
    )
    rc = mod.main()
    assert rc == 0
    # Report file should still exist (best-effort write)
    files = list(tmp_path.glob("vn_daily_brief_*.md"))
    assert len(files) == 1
