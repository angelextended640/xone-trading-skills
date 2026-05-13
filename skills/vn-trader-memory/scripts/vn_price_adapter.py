"""vnstock-backed price adapter for MAE/MFE calculation.

Single-purpose: fetch daily close prices for a VN ticker between two dates.
Skips the first 2 trading sessions (T+0 / T+1) since the position is not
liquidatable until T+2.5 — using them in MAE/MFE would overstate excursions.

Falls back gracefully when vnstock is unavailable: ``get_daily_closes()``
returns an empty list and the postmortem records ``mae_mfe_source = "manual"``.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Skip T+0 (entry day) and T+1 — the position can only be sold from T+2.5.
DEFAULT_SKIP_SESSIONS = 2


class VNPriceAdapter:
    """Daily-close fetcher used by vn_thesis_review.generate_postmortem()."""

    def __init__(self, source: str = "VCI", skip_sessions: int = DEFAULT_SKIP_SESSIONS):
        self.source = source
        self.skip_sessions = max(0, int(skip_sessions))

    def get_daily_closes(self, ticker: str, from_date: str, to_date: str) -> list[dict]:
        """Return [{"date": "YYYY-MM-DD", "close": float}, ...] oldest first.

        Tries direct vnstock import first, then falls back to invoking the
        vn-data-fetcher CLI in a subprocess. Returns [] on any failure.
        """
        rows = self._fetch_direct(ticker, from_date, to_date)
        if not rows:
            rows = self._fetch_via_subprocess(ticker, from_date, to_date)
        if not rows:
            return []

        # Sort oldest first, drop the first `skip_sessions` entries (T+0/T+1).
        rows.sort(key=lambda r: r["date"])
        return rows[self.skip_sessions :]

    def _fetch_direct(self, ticker: str, from_date: str, to_date: str) -> list[dict]:
        try:
            from vnstock import Quote
        except Exception as e:  # pragma: no cover - import-time
            logger.debug("vnstock not available for direct fetch: %s", e)
            return []

        try:
            df = Quote(symbol=ticker, source=self.source).history(
                start=from_date, end=to_date, interval="1D"
            )
        except Exception as e:
            logger.warning("vnstock direct fetch failed for %s: %s", ticker, e)
            return []

        if df is None or len(df) == 0:
            return []

        rows: list[dict] = []
        cols = {c.lower() for c in df.columns}
        date_col = "time" if "time" in cols else ("date" if "date" in cols else None)
        close_col = "close" if "close" in cols else None
        if not date_col or not close_col:
            logger.warning("Unexpected vnstock columns: %s", list(df.columns))
            return []

        for _, row in df.iterrows():
            d = str(row[date_col])[:10]
            try:
                c = float(row[close_col])
            except (TypeError, ValueError):
                continue
            rows.append({"date": d, "close": c})
        return rows

    def _fetch_via_subprocess(self, ticker: str, from_date: str, to_date: str) -> list[dict]:
        """Fall back to the vn-data-fetcher CLI; reads its JSON output."""
        repo_root = Path(__file__).resolve().parents[3]
        cli = repo_root / "skills" / "vn-data-fetcher" / "scripts" / "vn_data_fetcher.py"
        if not cli.exists():
            return []

        import json
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                sys.executable,
                str(cli),
                "ohlcv",
                "--symbol",
                ticker,
                "--start",
                from_date,
                "--end",
                to_date,
                "--interval",
                "1D",
                "--source",
                self.source,
                "--output-dir",
                tmpdir,
                "--no-cache",
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=60)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.debug("vn-data-fetcher subprocess failed for %s: %s", ticker, e)
                return []

            json_files = sorted(Path(tmpdir).glob(f"{ticker}_ohlcv_*.json"))
            if not json_files:
                return []
            with open(json_files[-1], encoding="utf-8") as f:
                payload = json.load(f)

        data = payload.get("data") or []
        rows = []
        for row in data:
            d = str(row.get("time", ""))[:10]
            close = row.get("close")
            if d and close is not None:
                try:
                    rows.append({"date": d, "close": float(close)})
                except (TypeError, ValueError):
                    continue
        return rows


class FixtureAdapter:
    """Test-only adapter that returns pre-canned close series."""

    def __init__(self, series: dict[str, list[dict]], skip_sessions: int = DEFAULT_SKIP_SESSIONS):
        self.series = series
        self.skip_sessions = max(0, int(skip_sessions))

    def get_daily_closes(self, ticker: str, from_date: str, to_date: str) -> list[dict]:
        rows = list(self.series.get(ticker, []))
        rows = [r for r in rows if from_date <= r["date"] <= to_date]
        rows.sort(key=lambda r: r["date"])
        return rows[self.skip_sessions :]
