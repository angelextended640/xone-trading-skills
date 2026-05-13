"""VN Data Fetcher — CLI wrapper around vnstock.

Subcommands:
  ohlcv         — historical open/high/low/close/volume
  info          — company listing info (industry, exchange, share count)
  foreign-flow  — net foreign buy/sell volume by day

Data source: vnstock (https://github.com/thinh-vu/vnstock).
Default upstream: VCI. Override via --source.
Offline test: pass --fixture <path-to-csv>.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

VN_TZ = timezone(timedelta(hours=7))  # Asia/Ho_Chi_Minh

VALID_SOURCES = {"VCI", "TCBS", "SSI", "MSN"}
VALID_INTERVALS = {"1m", "5m", "15m", "30m", "1H", "1D", "1W", "1M"}

# Cache location (relative to repo root)
DEFAULT_CACHE_DIR = Path("state/vn_market_data")


# ---------------------------------------------------------------------------
# vnstock lazy imports
# ---------------------------------------------------------------------------


def _import_vnstock_quote():
    """Import vnstock Quote class lazily. Raise ImportError with friendly hint."""
    try:
        from vnstock import Quote
    except ImportError as e:
        raise ImportError(
            "vnstock chưa được cài. Cài bằng: pip install -e \".[vn]\" "
            "hoặc pip install vnstock"
        ) from e
    return Quote


def _import_vnstock_company():
    try:
        from vnstock import Company
    except ImportError as e:
        raise ImportError(
            "vnstock chưa được cài. Cài bằng: pip install -e \".[vn]\""
        ) from e
    return Company


def _import_vnstock_finance():
    """Import vnstock Finance class lazily (or the Vnstock top-level wrapper)."""
    try:
        from vnstock import Finance
    except ImportError as e:
        raise ImportError(
            "vnstock chưa được cài. Cài bằng: pip install -e \".[vn]\""
        ) from e
    return Finance


def _import_vnstock_trading():
    """Import vnstock Trading class lazily (for foreign-flow snapshot)."""
    try:
        from vnstock import Trading
    except ImportError as e:
        raise ImportError(
            "vnstock chưa được cài. Cài bằng: pip install -e \".[vn]\""
        ) from e
    return Trading


def _import_pandas():
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError(
            "pandas chưa được cài. Sẽ được cài transitively với vnstock."
        ) from e
    return pd


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def cache_path(
    cache_dir: Path, symbol: str, source: str, interval: str, subcommand: str
) -> Path:
    """Build cache filename for a (symbol, source, interval, subcommand) tuple."""
    sym = symbol.upper()
    src = source.upper()
    return cache_dir / f"{sym}_{src}_{interval}_{subcommand}.csv"


def load_cache_csv(path: Path):
    """Load CSV cache. Return DataFrame or None if missing/empty."""
    if not path.exists() or path.stat().st_size == 0:
        return None
    pd = _import_pandas()
    try:
        df = pd.read_csv(path, parse_dates=["time"])
    except Exception:
        return None
    if df.empty:
        return None
    return df


def save_cache_csv(path: Path, df) -> None:
    """Save DataFrame to CSV cache, creating parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def filter_by_date_range(df, start: str, end: str):
    """Filter DataFrame to time within [start, end] inclusive."""
    pd = _import_pandas()
    if df is None or df.empty:
        return df
    start_ts = pd.to_datetime(start)
    end_ts = pd.to_datetime(end)
    mask = (df["time"] >= start_ts) & (df["time"] <= end_ts)
    return df.loc[mask].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Subcommand: ohlcv
# ---------------------------------------------------------------------------


def fetch_ohlcv_from_vnstock(symbol: str, source: str, start: str, end: str, interval: str):
    """Call vnstock.Quote.history. Return DataFrame."""
    Quote = _import_vnstock_quote()
    q = Quote(symbol=symbol, source=source)
    df = q.history(start=start, end=end, interval=interval)
    return df


def load_fixture(path: str):
    """Load fixture from CSV (or parquet if pyarrow installed).

    If the CSV has a `time` column, it is parsed as a date. Otherwise the
    CSV is loaded as-is (for non-OHLCV fixtures like dividends / fundamentals).
    """
    pd = _import_pandas()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Fixture không tồn tại: {path}")
    if p.suffix == ".parquet":
        return pd.read_parquet(p)
    # Peek at the header to decide whether to parse `time` as a date
    with open(p, encoding="utf-8") as f:
        header = f.readline().strip()
    parse_dates = ["time"] if "time" in header.split(",") else None
    return pd.read_csv(p, parse_dates=parse_dates)


def get_ohlcv(
    symbol: str,
    source: str,
    start: str,
    end: str,
    interval: str,
    cache_dir: Path,
    use_cache: bool,
    fixture: str | None,
) -> tuple[Any, str]:
    """Return (DataFrame, cache_status) where status ∈ {hit, miss, fixture}."""
    if fixture:
        df = load_fixture(fixture)
        df = filter_by_date_range(df, start, end)
        return df, "fixture"

    cache_file = cache_path(cache_dir, symbol, source, interval, "ohlcv")

    if use_cache:
        cached = load_cache_csv(cache_file)
        if cached is not None:
            filtered = filter_by_date_range(cached, start, end)
            cached_start = cached["time"].min()
            cached_end = cached["time"].max()
            pd = _import_pandas()
            req_start = pd.to_datetime(start)
            req_end = pd.to_datetime(end)
            # Hit if cache fully covers the requested range
            if cached_start <= req_start and cached_end >= req_end and not filtered.empty:
                return filtered, "hit"

    # Cache miss or disabled — fetch fresh
    df = fetch_ohlcv_from_vnstock(symbol, source, start, end, interval)
    if df is None or df.empty:
        raise RuntimeError(
            f"Không có dữ liệu cho {symbol} ({source}, {interval}) "
            f"từ {start} đến {end}"
        )

    if use_cache:
        save_cache_csv(cache_file, df)

    return df, "miss"


def serialize_ohlcv(df) -> list[dict]:
    """Convert DataFrame rows to list of dicts with ISO date strings."""
    out = []
    for _, row in df.iterrows():
        out.append(
            {
                "time": row["time"].strftime("%Y-%m-%d")
                if hasattr(row["time"], "strftime")
                else str(row["time"]),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
            }
        )
    return out


def run_ohlcv(args: argparse.Namespace) -> dict:
    symbols = [s.strip().upper() for s in args.symbols.split(",")] if args.symbols else [args.symbol.upper()]
    cache_dir = Path(args.cache_dir)
    results = {}
    cache_statuses = {}

    for sym in symbols:
        df, status = get_ohlcv(
            sym,
            args.source,
            args.start,
            args.end,
            args.interval,
            cache_dir,
            use_cache=not args.no_cache,
            fixture=args.fixture if len(symbols) == 1 else None,
        )
        results[sym] = serialize_ohlcv(df)
        cache_statuses[sym] = status

    output = {
        "schema_version": "1.0",
        "subcommand": "ohlcv",
        "source": args.source,
        "interval": args.interval,
        "range": {"start": args.start, "end": args.end},
        "fetched_at": datetime.now(VN_TZ).isoformat(),
        "cache_statuses": cache_statuses,
    }

    if len(symbols) == 1:
        sym = symbols[0]
        output["symbol"] = sym
        output["row_count"] = len(results[sym])
        output["cache_status"] = cache_statuses[sym]
        output["data"] = results[sym]
    else:
        output["symbols"] = symbols
        output["row_counts"] = {s: len(results[s]) for s in symbols}
        output["data"] = results

    return output


# ---------------------------------------------------------------------------
# Subcommand: info
# ---------------------------------------------------------------------------


def run_info(args: argparse.Namespace) -> dict:
    """Fetch listing info for a symbol via vnstock.Company."""
    sym = args.symbol.upper()
    if args.fixture:
        with open(args.fixture, encoding="utf-8") as f:
            fixture_data = json.load(f)
        return {
            "schema_version": "1.0",
            "subcommand": "info",
            "symbol": sym,
            "source": args.source,
            "fetched_at": datetime.now(VN_TZ).isoformat(),
            "cache_status": "fixture",
            **fixture_data,
        }

    Company = _import_vnstock_company()
    company = Company(symbol=sym, source=args.source)

    # vnstock exposes overview() returning a DataFrame with one row.
    try:
        overview_df = company.overview()
    except Exception as e:
        raise RuntimeError(f"Không lấy được info cho {sym}: {e}") from e

    if overview_df is None or overview_df.empty:
        raise RuntimeError(f"Info trống cho {sym}")

    row = overview_df.iloc[0].to_dict()

    return {
        "schema_version": "1.0",
        "subcommand": "info",
        "symbol": sym,
        "source": args.source,
        "fetched_at": datetime.now(VN_TZ).isoformat(),
        "cache_status": "miss",
        "overview": {k: (v if not _is_nan(v) else None) for k, v in row.items()},
    }


def _is_nan(v) -> bool:
    try:
        import math

        return isinstance(v, float) and math.isnan(v)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Subcommand: dividends
# ---------------------------------------------------------------------------


def serialize_dividends(df) -> list[dict]:
    """Convert vnstock dividends DataFrame to a list of dicts.

    vnstock's `Company().dividends()` schema varies by source. Common columns
    include `exercise_date` / `cash_year` / `cash_dividend_percentage` /
    `issue_method`. We normalise to a shape compatible with
    `vn-dividend-screener`'s universe schema: {year, type=cash|stock,
    amount_vnd_per_share or ratio, raw}.
    """
    out: list[dict] = []
    if df is None:
        return out
    # Try common column conventions; fall back to passthrough.
    for _, row in df.iterrows():
        rec: dict = {"raw": {str(k): _safe(v) for k, v in row.items()}}
        # Year extraction
        year = (
            row.get("cash_year")
            or row.get("year")
            or (
                _parse_year(row.get("exercise_date"))
                if "exercise_date" in row
                else None
            )
        )
        if year is not None:
            try:
                rec["year"] = int(year)
            except (TypeError, ValueError):
                pass
        # Type: cash vs stock
        method = (
            str(row.get("issue_method", "")).lower()
            or str(row.get("type", "")).lower()
        )
        if "cash" in method or "tien" in method or "tiền" in method:
            rec["type"] = "cash"
            # Cash dividend amount: try multiple common columns
            amount = (
                row.get("cash_dividend_percentage")
                or row.get("amount_vnd_per_share")
                or row.get("cash_per_share")
            )
            if amount is not None and not _is_nan(amount):
                # vnstock sometimes returns dividend % of par (10,000 VND) — convert
                if isinstance(amount, (int, float)) and 0 < amount < 200:
                    # If value < 200, likely a % (e.g., 25 = 25% × par 10,000 = 2,500 VND)
                    rec["amount_vnd_per_share"] = int(round(float(amount) * 100))
                else:
                    rec["amount_vnd_per_share"] = int(round(float(amount)))
        elif "stock" in method or "co_phieu" in method or "cổ phiếu" in method:
            rec["type"] = "stock"
            ratio = row.get("ratio") or row.get("issue_ratio")
            if ratio is not None and not _is_nan(ratio):
                rec["ratio"] = float(ratio)
        else:
            rec["type"] = "unknown"
        out.append(rec)
    return out


def _safe(v):
    """JSON-safe value (handle pandas NaN, Timestamp, etc.)."""
    if _is_nan(v):
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    if isinstance(v, (int, float, str, bool)) or v is None:
        return v
    return str(v)


def _parse_year(value) -> int | None:
    if value is None or _is_nan(value):
        return None
    s = str(value)
    if len(s) >= 4 and s[:4].isdigit():
        return int(s[:4])
    return None


def run_dividends(args: argparse.Namespace) -> dict:
    sym = args.symbol.upper()
    if args.fixture:
        df = load_fixture(args.fixture)
        rows = serialize_dividends(df)
        return {
            "schema_version": "1.0",
            "subcommand": "dividends",
            "symbol": sym,
            "source": args.source,
            "fetched_at": datetime.now(VN_TZ).isoformat(),
            "cache_status": "fixture",
            "row_count": len(rows),
            "data": rows,
        }

    # Try cache
    cache_file = cache_path(Path(args.cache_dir), sym, args.source, "all", "dividends")
    cached = None
    if not args.no_cache:
        cached = load_cache_csv(cache_file)
    if cached is not None:
        rows = serialize_dividends(cached)
        return {
            "schema_version": "1.0",
            "subcommand": "dividends",
            "symbol": sym,
            "source": args.source,
            "fetched_at": datetime.now(VN_TZ).isoformat(),
            "cache_status": "hit",
            "row_count": len(rows),
            "data": rows,
        }

    Company = _import_vnstock_company()
    company = Company(symbol=sym, source=args.source)
    try:
        df = company.dividends()
    except Exception as e:
        raise RuntimeError(f"Không lấy được dividends cho {sym}: {e}") from e
    if df is None or df.empty:
        raise RuntimeError(f"Dividend history trống cho {sym}")

    if not args.no_cache:
        save_cache_csv(cache_file, df)

    rows = serialize_dividends(df)
    return {
        "schema_version": "1.0",
        "subcommand": "dividends",
        "symbol": sym,
        "source": args.source,
        "fetched_at": datetime.now(VN_TZ).isoformat(),
        "cache_status": "miss",
        "row_count": len(rows),
        "data": rows,
    }


# ---------------------------------------------------------------------------
# Subcommand: fundamentals
# ---------------------------------------------------------------------------


def serialize_fundamentals(df, period: str) -> list[dict]:
    """Convert vnstock Finance().ratio() DataFrame to JSON-safe records."""
    out: list[dict] = []
    if df is None or df.empty:
        return out
    for _, row in df.iterrows():
        out.append({str(k): _safe(v) for k, v in row.items()})
    return out


def run_fundamentals(args: argparse.Namespace) -> dict:
    sym = args.symbol.upper()
    period = args.period
    if args.fixture:
        df = load_fixture(args.fixture)
        rows = serialize_fundamentals(df, period)
        return {
            "schema_version": "1.0",
            "subcommand": "fundamentals",
            "symbol": sym,
            "source": args.source,
            "period": period,
            "fetched_at": datetime.now(VN_TZ).isoformat(),
            "cache_status": "fixture",
            "row_count": len(rows),
            "data": rows,
        }

    cache_file = cache_path(
        Path(args.cache_dir), sym, args.source, period, "fundamentals"
    )
    cached = None
    if not args.no_cache:
        cached = load_cache_csv(cache_file)
    if cached is not None:
        rows = serialize_fundamentals(cached, period)
        return {
            "schema_version": "1.0",
            "subcommand": "fundamentals",
            "symbol": sym,
            "source": args.source,
            "period": period,
            "fetched_at": datetime.now(VN_TZ).isoformat(),
            "cache_status": "hit",
            "row_count": len(rows),
            "data": rows,
        }

    Finance = _import_vnstock_finance()
    finance = Finance(symbol=sym, source=args.source)
    try:
        df = finance.ratio(period=period)
    except Exception as e:
        raise RuntimeError(f"Không lấy được fundamentals cho {sym}: {e}") from e
    if df is None or df.empty:
        raise RuntimeError(f"Fundamentals trống cho {sym}")

    if not args.no_cache:
        save_cache_csv(cache_file, df)

    rows = serialize_fundamentals(df, period)
    return {
        "schema_version": "1.0",
        "subcommand": "fundamentals",
        "symbol": sym,
        "source": args.source,
        "period": period,
        "fetched_at": datetime.now(VN_TZ).isoformat(),
        "cache_status": "miss",
        "row_count": len(rows),
        "data": rows,
    }


# ---------------------------------------------------------------------------
# Subcommand: foreign-flow (snapshot via Trading.price_board, no daily series)
# ---------------------------------------------------------------------------


def run_foreign_flow(args: argparse.Namespace) -> dict:
    """Fetch a foreign-flow snapshot via Trading().price_board().

    Note: vnstock does NOT expose a unified daily-series API for foreign
    net buy/sell across all upstream sources. This subcommand returns a
    point-in-time snapshot only. For daily history, use
    `vn-foreign-room-tracker record` with manually-curated input.
    """
    sym = args.symbol.upper()
    if args.fixture:
        with open(args.fixture, encoding="utf-8") as f:
            fixture = json.load(f)
        return {
            "schema_version": "1.0",
            "subcommand": "foreign-flow",
            "symbol": sym,
            "source": args.source,
            "fetched_at": datetime.now(VN_TZ).isoformat(),
            "cache_status": "fixture",
            "mode": "snapshot",
            **fixture,
        }

    Trading = _import_vnstock_trading()
    pd = _import_pandas()
    try:
        trading = Trading(symbol=sym, source=args.source)
        df = trading.price_board([sym])
    except Exception as e:
        raise RuntimeError(
            f"Không lấy được snapshot foreign-flow cho {sym}: {e}. "
            f"vnstock không có daily-series endpoint thống nhất — dùng "
            f"`vn-foreign-room-tracker record` với CSV thủ công để build history."
        ) from e

    if df is None or df.empty:
        raise RuntimeError(f"Snapshot rỗng cho {sym}")

    row = df.iloc[0].to_dict()
    serial = {str(k): _safe(v) for k, v in row.items()}

    return {
        "schema_version": "1.0",
        "subcommand": "foreign-flow",
        "symbol": sym,
        "source": args.source,
        "fetched_at": datetime.now(VN_TZ).isoformat(),
        "cache_status": "miss",
        "mode": "snapshot",
        "snapshot": serial,
        "note": (
            "Point-in-time snapshot only. For daily series, use "
            "vn-foreign-room-tracker with manually-curated CSV input."
        ),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def default_start_date(days_back: int = 365) -> str:
    return (datetime.now(VN_TZ) - timedelta(days=days_back)).strftime("%Y-%m-%d")


def default_end_date() -> str:
    return datetime.now(VN_TZ).strftime("%Y-%m-%d")


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--source",
        default="VCI",
        choices=sorted(VALID_SOURCES),
        help="Upstream data source (mặc định VCI)",
    )
    parser.add_argument(
        "--cache-dir",
        default=str(DEFAULT_CACHE_DIR),
        help=f"Thư mục cache (mặc định {DEFAULT_CACHE_DIR})",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bỏ qua cache, fetch tươi",
    )
    parser.add_argument(
        "--fixture",
        help="Đường dẫn fixture (CSV cho ohlcv, JSON cho info/foreign-flow) cho test offline",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/",
        help="Thư mục xuất báo cáo (mặc định reports/)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Lấy dữ liệu thị trường CK Việt Nam qua vnstock"
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    # ohlcv
    p_ohlcv = sub.add_parser("ohlcv", help="OHLCV lịch sử")
    sym_group = p_ohlcv.add_mutually_exclusive_group(required=True)
    sym_group.add_argument("--symbol", help="Mã CP đơn lẻ (ví dụ VIC)")
    sym_group.add_argument(
        "--symbols",
        help="Nhiều mã cách nhau bởi dấu phẩy (ví dụ VIC,HPG,VNM)",
    )
    p_ohlcv.add_argument(
        "--start",
        default=default_start_date(),
        help="Ngày bắt đầu (YYYY-MM-DD, mặc định 365 ngày trước)",
    )
    p_ohlcv.add_argument(
        "--end",
        default=default_end_date(),
        help="Ngày kết thúc (YYYY-MM-DD, mặc định hôm nay)",
    )
    p_ohlcv.add_argument(
        "--interval",
        default="1D",
        choices=sorted(VALID_INTERVALS),
        help="Tần suất nến (mặc định 1D)",
    )
    add_common_args(p_ohlcv)

    # info
    p_info = sub.add_parser("info", help="Thông tin niêm yết")
    p_info.add_argument("--symbol", required=True, help="Mã CP")
    add_common_args(p_info)

    # dividends
    p_div = sub.add_parser("dividends", help="Lịch sử cổ tức (cash + stock)")
    p_div.add_argument("--symbol", required=True, help="Mã CP")
    add_common_args(p_div)

    # fundamentals
    p_fund = sub.add_parser("fundamentals", help="P/E, P/B, ROE, EPS, payout ratio")
    p_fund.add_argument("--symbol", required=True, help="Mã CP")
    p_fund.add_argument(
        "--period",
        default="quarter",
        choices=["quarter", "year"],
        help="Tần suất report (mặc định quarter)",
    )
    add_common_args(p_fund)

    # foreign-flow (snapshot only)
    p_ff = sub.add_parser(
        "foreign-flow",
        help="Snapshot khối ngoại mua/bán (point-in-time, không có daily series)",
    )
    p_ff.add_argument("--symbol", required=True, help="Mã CP")
    p_ff.add_argument(
        "--days",
        type=int,
        default=30,
        help="(Unused — snapshot only) Số phiên gần nhất kept for backward compat",
    )
    add_common_args(p_ff)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.subcommand == "ohlcv":
            result = run_ohlcv(args)
            tag = "ohlcv"
        elif args.subcommand == "info":
            result = run_info(args)
            tag = "info"
        elif args.subcommand == "dividends":
            result = run_dividends(args)
            tag = "dividends"
        elif args.subcommand == "fundamentals":
            result = run_fundamentals(args)
            tag = "fundamentals"
        elif args.subcommand == "foreign-flow":
            result = run_foreign_flow(args)
            tag = "foreign_flow"
        else:
            parser.error(f"Unknown subcommand: {args.subcommand}")
            return  # unreachable
    except ImportError as e:
        print(f"Lỗi import: {e}", file=sys.stderr)
        sys.exit(2)
    except (RuntimeError, FileNotFoundError, ValueError, NotImplementedError) as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

    # Write output
    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now(VN_TZ).strftime("%Y-%m-%d_%H%M%S")
    sym_tag = (
        result.get("symbol")
        or "_".join(result.get("symbols", ["batch"]))
    )
    sym_tag = sym_tag if len(sym_tag) <= 40 else "batch"

    json_path = os.path.join(args.output_dir, f"vn_{tag}_{sym_tag}_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON: {json_path}")

    # For OHLCV single-symbol, also emit a flat CSV for convenience
    if args.subcommand == "ohlcv" and "data" in result and isinstance(result["data"], list):
        csv_path = os.path.join(args.output_dir, f"vn_ohlcv_{sym_tag}_{timestamp}.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("time,open,high,low,close,volume\n")
            for row in result["data"]:
                f.write(
                    f"{row['time']},{row['open']},{row['high']},"
                    f"{row['low']},{row['close']},{row['volume']}\n"
                )
        print(f"CSV: {csv_path}")

    # Summary
    if args.subcommand == "ohlcv":
        if "row_count" in result:
            print(
                f"\n{result['symbol']}: {result['row_count']} rows, "
                f"cache {result['cache_status']}"
            )
        else:
            for s in result["symbols"]:
                print(
                    f"{s}: {result['row_counts'][s]} rows, "
                    f"cache {result['cache_statuses'][s]}"
                )


if __name__ == "__main__":
    main()
