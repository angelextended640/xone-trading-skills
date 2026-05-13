"""Tests for vn-data-fetcher.

All tests use --fixture mode — no live vnstock calls.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from vn_data_fetcher import (
    DEFAULT_CACHE_DIR,
    VALID_INTERVALS,
    VALID_SOURCES,
    VN_TZ,
    build_parser,
    cache_path,
    filter_by_date_range,
    get_ohlcv,
    load_cache_csv,
    load_fixture,
    save_cache_csv,
    serialize_ohlcv,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"
VIC_CSV = FIXTURE_DIR / "vic_daily.csv"
VIC_INFO = FIXTURE_DIR / "vic_info.json"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_vn_timezone(self):
        # UTC+7
        assert VN_TZ.utcoffset(None).total_seconds() == 7 * 3600

    def test_valid_sources(self):
        assert "VCI" in VALID_SOURCES
        assert "TCBS" in VALID_SOURCES

    def test_valid_intervals(self):
        assert "1D" in VALID_INTERVALS
        assert "1W" in VALID_INTERVALS

    def test_default_cache_dir(self):
        assert str(DEFAULT_CACHE_DIR).endswith("vn_market_data")


# ---------------------------------------------------------------------------
# Cache path & I/O
# ---------------------------------------------------------------------------


class TestCachePath:
    def test_uppercase_normalization(self, tmp_path):
        p = cache_path(tmp_path, "vic", "vci", "1D", "ohlcv")
        assert p.name == "VIC_VCI_1D_ohlcv.csv"
        assert p.parent == tmp_path

    def test_different_interval_different_path(self, tmp_path):
        p1 = cache_path(tmp_path, "VIC", "VCI", "1D", "ohlcv")
        p2 = cache_path(tmp_path, "VIC", "VCI", "1W", "ohlcv")
        assert p1 != p2


class TestCacheIO:
    def test_load_missing_returns_none(self, tmp_path):
        missing = tmp_path / "nonexistent.csv"
        assert load_cache_csv(missing) is None

    def test_save_then_load_roundtrip(self, tmp_path):
        df_orig = load_fixture(str(VIC_CSV))
        cache_file = tmp_path / "VIC_VCI_1D_ohlcv.csv"
        save_cache_csv(cache_file, df_orig)
        assert cache_file.exists()

        loaded = load_cache_csv(cache_file)
        assert loaded is not None
        assert len(loaded) == len(df_orig)
        assert list(loaded.columns) == ["time", "open", "high", "low", "close", "volume"]


# ---------------------------------------------------------------------------
# Date filtering
# ---------------------------------------------------------------------------


class TestDateFilter:
    def test_filter_within_range(self):
        df = load_fixture(str(VIC_CSV))
        filtered = filter_by_date_range(df, "2026-05-05", "2026-05-08")
        # Fixture has 2026-05-04, 05, 06, 07, 08, 09, 12 → expect 05, 06, 07, 08
        assert len(filtered) == 4
        assert str(filtered["time"].iloc[0].date()) == "2026-05-05"
        assert str(filtered["time"].iloc[-1].date()) == "2026-05-08"

    def test_filter_exact_endpoint_inclusive(self):
        df = load_fixture(str(VIC_CSV))
        filtered = filter_by_date_range(df, "2026-05-04", "2026-05-04")
        assert len(filtered) == 1

    def test_filter_outside_range_empty(self):
        df = load_fixture(str(VIC_CSV))
        filtered = filter_by_date_range(df, "2027-01-01", "2027-01-31")
        assert len(filtered) == 0


# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------


class TestLoadFixture:
    def test_csv_load(self):
        df = load_fixture(str(VIC_CSV))
        assert len(df) == 7
        assert list(df.columns) == ["time", "open", "high", "low", "close", "volume"]

    def test_missing_fixture_raises(self):
        with pytest.raises(FileNotFoundError):
            load_fixture("/nonexistent/path.csv")


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


class TestSerialize:
    def test_serialize_ohlcv_shape(self):
        df = load_fixture(str(VIC_CSV))
        rows = serialize_ohlcv(df)
        assert len(rows) == 7
        first = rows[0]
        assert first["time"] == "2026-05-04"
        assert first["open"] == 217.0
        assert first["close"] == 212.0
        assert first["volume"] == 3884000

    def test_types(self):
        df = load_fixture(str(VIC_CSV))
        rows = serialize_ohlcv(df)
        for r in rows:
            assert isinstance(r["time"], str)
            assert isinstance(r["open"], float)
            assert isinstance(r["volume"], int)


# ---------------------------------------------------------------------------
# get_ohlcv — fixture mode
# ---------------------------------------------------------------------------


class TestGetOhlcvFixture:
    def test_fixture_returns_status(self, tmp_path):
        df, status = get_ohlcv(
            symbol="VIC",
            source="VCI",
            start="2026-05-05",
            end="2026-05-08",
            interval="1D",
            cache_dir=tmp_path,
            use_cache=False,
            fixture=str(VIC_CSV),
        )
        assert status == "fixture"
        assert len(df) == 4  # 05-05 through 05-08

    def test_fixture_ignores_cache(self, tmp_path):
        # Even with use_cache=True, fixture wins
        df, status = get_ohlcv(
            symbol="VIC",
            source="VCI",
            start="2026-05-04",
            end="2026-05-12",
            interval="1D",
            cache_dir=tmp_path,
            use_cache=True,
            fixture=str(VIC_CSV),
        )
        assert status == "fixture"


# ---------------------------------------------------------------------------
# get_ohlcv — cache hit/miss
# ---------------------------------------------------------------------------


class TestGetOhlcvCache:
    def test_cache_hit_when_range_covered(self, tmp_path):
        # Pre-populate cache with full fixture data
        df_full = load_fixture(str(VIC_CSV))
        cache_file = cache_path(tmp_path, "VIC", "VCI", "1D", "ohlcv")
        save_cache_csv(cache_file, df_full)

        # Request a subset → should hit cache
        df, status = get_ohlcv(
            symbol="VIC",
            source="VCI",
            start="2026-05-05",
            end="2026-05-08",
            interval="1D",
            cache_dir=tmp_path,
            use_cache=True,
            fixture=None,
        )
        assert status == "hit"
        assert len(df) == 4

    def test_no_cache_flag_skips_cache(self, tmp_path):
        # Pre-populate cache
        df_full = load_fixture(str(VIC_CSV))
        cache_file = cache_path(tmp_path, "VIC", "VCI", "1D", "ohlcv")
        save_cache_csv(cache_file, df_full)

        # Mock the live fetch — it should be called even though cache exists
        with patch("vn_data_fetcher.fetch_ohlcv_from_vnstock", return_value=df_full):
            df, status = get_ohlcv(
                symbol="VIC",
                source="VCI",
                start="2026-05-05",
                end="2026-05-08",
                interval="1D",
                cache_dir=tmp_path,
                use_cache=False,
                fixture=None,
            )
            assert status == "miss"  # fresh fetch

    def test_cache_miss_when_range_uncovered(self, tmp_path):
        # Cache only has 2026-05-04 to 2026-05-12; request earlier window
        df_full = load_fixture(str(VIC_CSV))
        cache_file = cache_path(tmp_path, "VIC", "VCI", "1D", "ohlcv")
        save_cache_csv(cache_file, df_full)

        with patch("vn_data_fetcher.fetch_ohlcv_from_vnstock", return_value=df_full):
            _, status = get_ohlcv(
                symbol="VIC",
                source="VCI",
                start="2026-01-01",  # before cache start
                end="2026-05-12",
                interval="1D",
                cache_dir=tmp_path,
                use_cache=True,
                fixture=None,
            )
            assert status == "miss"


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------


class TestArgParser:
    def test_ohlcv_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "ohlcv",
                "--symbol", "VIC",
                "--start", "2026-05-01",
                "--end", "2026-05-12",
            ]
        )
        assert args.subcommand == "ohlcv"
        assert args.symbol == "VIC"
        assert args.source == "VCI"  # default
        assert args.interval == "1D"  # default

    def test_ohlcv_symbols_mutex_with_symbol(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(
                ["ohlcv", "--symbol", "VIC", "--symbols", "HPG,VNM"]
            )

    def test_info_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["info", "--symbol", "VIC"])
        assert args.subcommand == "info"

    def test_invalid_source_rejected(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["ohlcv", "--symbol", "VIC", "--source", "NOTAREALSOURCE"])

    def test_invalid_interval_rejected(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["ohlcv", "--symbol", "VIC", "--interval", "2H"])


# ---------------------------------------------------------------------------
# Info subcommand fixture
# ---------------------------------------------------------------------------


class TestInfoFixture:
    def test_info_with_fixture(self, tmp_path, capsys):
        from vn_data_fetcher import run_info

        class Args:
            symbol = "VIC"
            source = "VCI"
            fixture = str(VIC_INFO)
            cache_dir = str(tmp_path)
            no_cache = False
            output_dir = str(tmp_path)

        result = run_info(Args())
        assert result["symbol"] == "VIC"
        assert result["cache_status"] == "fixture"
        assert result["overview"]["exchange"] == "HOSE"
        assert result["overview"]["industry"] == "Bất động sản"


# ---------------------------------------------------------------------------
# Dividends subcommand
# ---------------------------------------------------------------------------

VIC_DIVIDENDS_CSV = FIXTURE_DIR / "vic_dividends.csv"
VIC_FUNDAMENTALS_CSV = FIXTURE_DIR / "vic_fundamentals.csv"
VIC_FF_SNAPSHOT = FIXTURE_DIR / "vic_foreign_flow_snapshot.json"


class TestDividends:
    def test_dividends_fixture(self, tmp_path):
        from vn_data_fetcher import run_dividends

        class Args:
            symbol = "VIC"
            source = "VCI"
            fixture = str(VIC_DIVIDENDS_CSV)
            cache_dir = str(tmp_path)
            no_cache = False
            output_dir = str(tmp_path)

        result = run_dividends(Args())
        assert result["symbol"] == "VIC"
        assert result["cache_status"] == "fixture"
        assert result["row_count"] == 5
        # Fixture has 5 rows: cash 2025/2024/2023/2022 + stock 2024
        types = [r["type"] for r in result["data"]]
        assert types.count("cash") == 4
        assert types.count("stock") == 1
        # Cash amounts converted from percentage to VND
        # cash_dividend_percentage 25 → 25% × par 10000 = 2500 VND
        cash_2025 = next(r for r in result["data"] if r.get("year") == 2025 and r["type"] == "cash")
        assert cash_2025["amount_vnd_per_share"] == 2500
        # Stock dividend ratio preserved
        stock = next(r for r in result["data"] if r["type"] == "stock")
        assert stock["ratio"] == 0.10


class TestFundamentals:
    def test_fundamentals_fixture(self, tmp_path):
        from vn_data_fetcher import run_fundamentals

        class Args:
            symbol = "VIC"
            source = "VCI"
            period = "quarter"
            fixture = str(VIC_FUNDAMENTALS_CSV)
            cache_dir = str(tmp_path)
            no_cache = False
            output_dir = str(tmp_path)

        result = run_fundamentals(Args())
        assert result["symbol"] == "VIC"
        assert result["period"] == "quarter"
        assert result["cache_status"] == "fixture"
        assert result["row_count"] == 4
        first = result["data"][0]
        assert first["period"] == "2026Q1"
        # ROE preserved
        assert float(first["roe"]) == 18.2


class TestForeignFlow:
    def test_foreign_flow_fixture_snapshot(self, tmp_path):
        from vn_data_fetcher import run_foreign_flow

        class Args:
            symbol = "VIC"
            source = "VCI"
            days = 30
            fixture = str(VIC_FF_SNAPSHOT)
            cache_dir = str(tmp_path)
            no_cache = False
            output_dir = str(tmp_path)

        result = run_foreign_flow(Args())
        assert result["symbol"] == "VIC"
        assert result["mode"] == "snapshot"
        assert result["cache_status"] == "fixture"
        assert result["snapshot"]["foreign_net_volume"] == 270000


class TestNewSubcommandsInParser:
    def test_dividends_in_parser(self):
        parser = build_parser()
        args = parser.parse_args(["dividends", "--symbol", "VIC"])
        assert args.subcommand == "dividends"

    def test_fundamentals_in_parser(self):
        parser = build_parser()
        args = parser.parse_args(["fundamentals", "--symbol", "VIC", "--period", "year"])
        assert args.subcommand == "fundamentals"
        assert args.period == "year"

    def test_fundamentals_invalid_period(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["fundamentals", "--symbol", "VIC", "--period", "weekly"])

    def test_foreign_flow_in_parser(self):
        parser = build_parser()
        args = parser.parse_args(["foreign-flow", "--symbol", "VIC"])
        assert args.subcommand == "foreign-flow"
