"""VN Daily Brief — composite morning routine orchestrator.

Wraps three deterministic VN skills (sector-analyst, foreign-room-tracker report,
portfolio-manager summary) into a single command and emits a consolidated
markdown report under reports/vn_daily_brief_<date>.md.

By default failures are tolerated (best-effort orchestration). Pass `--strict`
to exit non-zero on any sub-skill failure.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

VN_TZ = timezone(timedelta(hours=7))

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def run_command(cmd: str | list[str]) -> tuple[bool, str]:
    """Run a sub-skill command. Returns (success, stdout-or-stderr).

    The function is intentionally tolerant — sub-skills may exit non-zero
    when state is empty (e.g. no portfolio yet). We surface stdout when
    available and stderr otherwise, but never raise.
    """
    if isinstance(cmd, str):
        # shlex on POSIX-style command strings (works on Windows for our
        # purposes because we only quote paths via shlex.quote).
        argv = shlex.split(cmd, posix=True)
    else:
        argv = list(cmd)

    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as e:
        return False, f"Error: command not found — {e}"

    if result.returncode == 0:
        return True, result.stdout or ""
    body = result.stdout or ""
    if result.stderr:
        body += ("\n" if body else "") + result.stderr.strip()
    return False, body or f"sub-skill exited with code {result.returncode}"


def build_sector_cmd(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(PROJECT_ROOT / "skills" / "vn-sector-analyst" / "scripts" / "vn_sector_analyst.py"),
        "--ohlcv-glob",
        args.ohlcv_glob,
    ]


def build_room_cmd(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(PROJECT_ROOT / "skills" / "vn-foreign-room-tracker" / "scripts" / "vn_foreign_room.py"),
        "report",
        "--state-dir",
        args.room_state_dir,
        "--lookback-days",
        str(args.lookback_days),
    ]


def build_portfolio_cmd(args: argparse.Namespace) -> list[str]:
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "skills" / "vn-portfolio-manager" / "scripts" / "vn_portfolio_manager.py"),
        "summary",
        "--state-dir",
        args.portfolio_state_dir,
        "--account-size",
        str(args.account_size),
    ]
    if args.prices:
        cmd += ["--prices", args.prices]
    return cmd


def assemble_brief(args: argparse.Namespace) -> dict:
    """Run all sub-skills and return a structured result dict."""
    as_of = datetime.now(VN_TZ).strftime("%Y-%m-%d")
    timestamp = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")

    sections = []

    # 1. Sector rotation
    ok_s, out_s = run_command(build_sector_cmd(args))
    sections.append(
        {
            "title": "1. Rotation ngành (vn-sector-analyst)",
            "ok": ok_s,
            "body": out_s,
        }
    )

    # 2. Foreign room delta
    ok_r, out_r = run_command(build_room_cmd(args))
    sections.append(
        {
            "title": "2. Biến động Room ngoại (vn-foreign-room-tracker report)",
            "ok": ok_r,
            "body": out_r,
        }
    )

    # 3. Portfolio summary
    ok_p, out_p = run_command(build_portfolio_cmd(args))
    sections.append(
        {
            "title": "3. Trạng thái Danh mục (vn-portfolio-manager summary)",
            "ok": ok_p,
            "body": out_p,
        }
    )

    failures = [s for s in sections if not s["ok"]]

    return {
        "as_of": as_of,
        "timestamp": timestamp,
        "sections": sections,
        "failures": failures,
        "all_ok": len(failures) == 0,
    }


def render_markdown(brief: dict) -> str:
    """Render the brief dict as a single markdown report."""
    lines = [
        f"# VN Daily Brief — {brief['as_of']}",
        "",
        f"_Generated at {brief['timestamp']} (Asia/Ho_Chi_Minh, UTC+7)_",
        "",
    ]
    if not brief["all_ok"]:
        lines.append(
            f"> ⚠️  {len(brief['failures'])} sub-skill(s) báo lỗi — xem chi tiết bên dưới."
        )
        lines.append("")

    for sec in brief["sections"]:
        status = "✅" if sec["ok"] else "⚠️"
        lines.append(f"## {status} {sec['title']}")
        lines.append("")
        body = sec["body"].strip() or "_(không có output)_"
        # Wrap code-like output in a fenced block to preserve formatting
        if any(line.startswith("===") or line.startswith("---") for line in body.splitlines()):
            lines.append("```")
            lines.append(body)
            lines.append("```")
        else:
            lines.append(body)
        lines.append("")

    return "\n".join(lines) + "\n"


def write_report(brief: dict, output_dir: str) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"vn_daily_brief_{brief['as_of']}.md"
    md_path.write_text(render_markdown(brief), encoding="utf-8")
    return md_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VN Daily Brief — composite morning routine orchestrator"
    )
    parser.add_argument(
        "--ohlcv-glob",
        default="reports/vn_ohlcv_*.json",
        help="Glob for vn-sector-analyst OHLCV inputs",
    )
    parser.add_argument(
        "--room-state-dir",
        default="state/vn_foreign_room",
        help="State dir for vn-foreign-room-tracker",
    )
    parser.add_argument(
        "--portfolio-state-dir",
        default="state/vn_portfolio",
        help="State dir for vn-portfolio-manager",
    )
    parser.add_argument(
        "--prices",
        default="",
        help="Comma-separated SYM:PRICE for portfolio mark-to-market",
    )
    parser.add_argument(
        "--account-size",
        default="1000000000",
        help="Account size in VND (for vn-portfolio-manager)",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=1,
        help="Foreign-room comparison window (days)",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/",
        help="Output directory for the consolidated report",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any sub-skill fails",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    brief = assemble_brief(args)
    md_path = write_report(brief, args.output_dir)

    print(f"Báo cáo: {md_path}")
    print(f"Sections OK: {sum(1 for s in brief['sections'] if s['ok'])}/{len(brief['sections'])}")
    if brief["failures"]:
        print(f"Sub-skill lỗi: {[s['title'] for s in brief['failures']]}", file=sys.stderr)
        if args.strict:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
