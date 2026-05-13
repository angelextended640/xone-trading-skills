"""Tests for vn-portfolio-manager."""

import argparse
import json
from pathlib import Path

import pytest

from vn_portfolio_manager import (
    DEFAULT_BROKER_FEE_PCT,
    DEFAULT_SALE_TAX_PCT,
    Holding,
    buy_fee,
    hold_days_between,
    load_closed,
    load_holdings,
    load_prices_file,
    net_pnl,
    parse_prices_cli,
    run_add,
    run_remove,
    run_status,
    run_summary,
    save_holdings,
    sell_fee_and_tax,
)


# ---------------------------------------------------------------------------
# Fee + tax math
# ---------------------------------------------------------------------------


class TestFees:
    def test_buy_fee_basic(self):
        # 1000 CP × 45000 = 45,000,000; fee 0.15% = 67,500
        assert buy_fee(45_000_000) == 67_500

    def test_sell_fee_and_tax(self):
        fee, tax = sell_fee_and_tax(45_000_000)
        # 0.15% fee + 0.1% tax on 45M
        assert fee == 67_500
        assert tax == 45_000


class TestNetPnl:
    def test_vic_winner(self):
        # 1000 CP, buy 45k, sell 48k → gross = 3M
        # fees buy = 67,500; fees sell = 72,000; tax sell = 48,000
        # net = 3,000,000 - 67,500 - 72,000 - 48,000 = 2,812,500
        result = net_pnl(1000, 45_000, 48_000)
        assert result["gross_pnl_vnd"] == 3_000_000
        assert result["fees_vnd"] == 67_500 + 72_000  # 139,500
        assert result["tax_vnd"] == 48_000
        assert result["net_pnl_vnd"] == 2_812_500
        # net_pnl_pct = 2,812,500 / 45,000,000 = 6.25%
        assert result["net_pnl_pct"] == 6.25

    def test_loser(self):
        # Buy 45k sell 43k, 1000 CP → gross -2M
        # Sale tax still applies even on loss!
        result = net_pnl(1000, 45_000, 43_000)
        assert result["gross_pnl_vnd"] == -2_000_000
        # fees: buy 67,500 + sell 64,500 = 132,000
        # tax: 43,000 (still 0.1% on sale value even if loss)
        assert result["fees_vnd"] == 132_000
        assert result["tax_vnd"] == 43_000
        assert result["net_pnl_vnd"] == -2_175_000  # -2M - 132k - 43k

    def test_breakeven_after_fees(self):
        """A small ~0.4% gain is essentially break-even after fees+tax."""
        # 1000 × 45,000 buy; sell at 45,180 (0.4% up)
        result = net_pnl(1000, 45_000, 45_180)
        # Should be near zero net
        assert abs(result["net_pnl_vnd"]) < 50_000  # within 50k VND


class TestHoldDays:
    def test_normal(self):
        assert hold_days_between("2026-05-04", "2026-05-13") == 9

    def test_same_day(self):
        assert hold_days_between("2026-05-04", "2026-05-04") == 0

    def test_invalid_returns_zero(self):
        assert hold_days_between("", "2026-05-13") == 0
        assert hold_days_between("not-a-date", "2026-05-13") == 0


# ---------------------------------------------------------------------------
# CSV state I/O
# ---------------------------------------------------------------------------


class TestCsvIO:
    def test_save_and_load_holdings_roundtrip(self, tmp_path):
        holdings = [
            Holding(
                symbol="VIC",
                exchange="hose",
                shares=3300,
                avg_price=45000,
                buy_date="2026-05-04",
                sector="Bất động sản",
                notes="VCP",
            ),
            Holding(
                symbol="HPG",
                exchange="hose",
                shares=2000,
                avg_price=28000,
                buy_date="2026-05-06",
                sector="Vật liệu",
            ),
        ]
        save_holdings(tmp_path, holdings)
        loaded = load_holdings(tmp_path)
        assert len(loaded) == 2
        assert loaded[0].symbol == "VIC"
        assert loaded[0].shares == 3300
        assert loaded[1].symbol == "HPG"
        assert loaded[0].sector == "Bất động sản"  # UTF-8 preserved

    def test_load_missing_returns_empty(self, tmp_path):
        assert load_holdings(tmp_path) == []
        assert load_closed(tmp_path) == []


# ---------------------------------------------------------------------------
# Price parsing
# ---------------------------------------------------------------------------


class TestPriceParsing:
    def test_cli_parse(self):
        prices = parse_prices_cli("VIC:46500,HPG:28500,FPT:142000")
        assert prices == {"VIC": 46500.0, "HPG": 28500.0, "FPT": 142000.0}

    def test_cli_uppercase(self):
        assert parse_prices_cli("vic:46500") == {"VIC": 46500.0}

    def test_cli_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_prices_cli("VIC=46500")

    def test_load_flat_json(self, tmp_path):
        path = tmp_path / "p.json"
        path.write_text('{"VIC": 46500, "HPG": 28500}', encoding="utf-8")
        prices = load_prices_file(str(path))
        assert prices == {"VIC": 46500.0, "HPG": 28500.0}

    def test_load_vn_data_fetcher_single_symbol(self, tmp_path):
        """Should extract last close from vn-data-fetcher single-symbol output."""
        path = tmp_path / "p.json"
        path.write_text(
            json.dumps(
                {
                    "symbol": "VIC",
                    "data": [
                        {"time": "2026-05-12", "close": 228.5},
                        {"time": "2026-05-13", "close": 230.0},
                    ],
                }
            ),
            encoding="utf-8",
        )
        prices = load_prices_file(str(path))
        assert prices == {"VIC": 230.0}

    def test_load_vn_data_fetcher_multi_symbol(self, tmp_path):
        path = tmp_path / "p.json"
        path.write_text(
            json.dumps(
                {
                    "symbols": ["VIC", "HPG"],
                    "data": {
                        "VIC": [{"close": 228.5}, {"close": 230.0}],
                        "HPG": [{"close": 27.5}, {"close": 28.0}],
                    },
                }
            ),
            encoding="utf-8",
        )
        prices = load_prices_file(str(path))
        assert prices == {"VIC": 230.0, "HPG": 28.0}


# ---------------------------------------------------------------------------
# Subcommand: add
# ---------------------------------------------------------------------------


def make_args(**kwargs):
    """Build an argparse.Namespace with portfolio-manager defaults."""
    defaults = dict(
        broker_fee_pct=DEFAULT_BROKER_FEE_PCT,
        sale_tax_pct=DEFAULT_SALE_TAX_PCT,
        prices=None,
        prices_file=None,
        notes="",
        sector="",
        account_size=None,
        max_position_pct=None,
        max_sector_pct=None,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddSubcommand:
    def test_add_new(self, tmp_path):
        args = make_args(
            symbol="VIC",
            exchange="hose",
            shares=3300,
            avg_price=45000.0,
            buy_date="2026-05-04",
            sector="Bất động sản",
            state_dir=str(tmp_path),
        )
        result = run_add(args)
        assert result["action"] == "added"
        assert result["symbol"] == "VIC"
        assert result["total_open_positions"] == 1

        # Verify CSV
        holdings = load_holdings(tmp_path)
        assert len(holdings) == 1
        assert holdings[0].symbol == "VIC"
        assert holdings[0].shares == 3300

    def test_add_averages_when_existing(self, tmp_path):
        # First buy 1000 @ 45,000
        args1 = make_args(
            symbol="VIC",
            exchange="hose",
            shares=1000,
            avg_price=45000.0,
            buy_date="2026-05-04",
            state_dir=str(tmp_path),
        )
        run_add(args1)

        # Second buy 1000 @ 47,000 → avg should be 46,000
        args2 = make_args(
            symbol="VIC",
            exchange="hose",
            shares=1000,
            avg_price=47000.0,
            buy_date="2026-05-10",
            state_dir=str(tmp_path),
        )
        result = run_add(args2)
        assert result["action"] == "averaged"

        holdings = load_holdings(tmp_path)
        assert len(holdings) == 1
        assert holdings[0].shares == 2000
        assert holdings[0].avg_price == 46000.0


# ---------------------------------------------------------------------------
# Subcommand: remove
# ---------------------------------------------------------------------------


class TestRemoveSubcommand:
    def test_remove_records_closed(self, tmp_path):
        # Add then remove
        run_add(
            make_args(
                symbol="VIC",
                exchange="hose",
                shares=1000,
                avg_price=45000.0,
                buy_date="2026-05-04",
                sector="Bất động sản",
                state_dir=str(tmp_path),
            )
        )
        result = run_remove(
            make_args(
                symbol="VIC",
                close_price=48000.0,
                close_date="2026-05-13",
                state_dir=str(tmp_path),
            )
        )
        closed = result["closed"]
        assert closed["symbol"] == "VIC"
        assert closed["gross_pnl_vnd"] == 3_000_000
        assert closed["net_pnl_vnd"] == 2_812_500
        assert closed["hold_days"] == 9

        # Holding removed
        assert len(load_holdings(tmp_path)) == 0
        # Closed appended
        assert len(load_closed(tmp_path)) == 1

    def test_remove_missing_symbol_raises(self, tmp_path):
        with pytest.raises(ValueError, match="VIC"):
            run_remove(
                make_args(
                    symbol="VIC",
                    close_price=48000.0,
                    close_date="2026-05-13",
                    state_dir=str(tmp_path),
                )
            )


# ---------------------------------------------------------------------------
# Subcommand: status
# ---------------------------------------------------------------------------


class TestStatusSubcommand:
    def test_status_with_prices(self, tmp_path):
        run_add(
            make_args(
                symbol="VIC",
                exchange="hose",
                shares=3300,
                avg_price=45000.0,
                buy_date="2026-05-04",
                sector="Bất động sản",
                state_dir=str(tmp_path),
            )
        )
        result = run_status(
            make_args(
                prices="VIC:46500",
                state_dir=str(tmp_path),
            )
        )
        assert len(result["positions"]) == 1
        pos = result["positions"][0]
        assert pos["symbol"] == "VIC"
        assert pos["current_price"] == 46500.0
        # market value = 3300 * 46500 = 153,450,000
        assert pos["market_value_vnd"] == 153_450_000
        # cost basis = 148,500,000; gross = 4,950,000
        assert pos["unrealized_gross_pnl_vnd"] == 4_950_000
        assert pos["unrealized_pnl_pct"] == round(4_950_000 / 148_500_000 * 100, 3)

    def test_status_reports_missing_prices(self, tmp_path):
        run_add(
            make_args(
                symbol="VIC",
                exchange="hose",
                shares=1000,
                avg_price=45000.0,
                buy_date="2026-05-04",
                state_dir=str(tmp_path),
            )
        )
        run_add(
            make_args(
                symbol="HPG",
                exchange="hose",
                shares=1000,
                avg_price=28000.0,
                buy_date="2026-05-06",
                state_dir=str(tmp_path),
            )
        )
        # Only provide VIC price
        result = run_status(
            make_args(prices="VIC:46500", state_dir=str(tmp_path))
        )
        assert result["missing_prices_for"] == ["HPG"]
        assert len(result["positions"]) == 1


# ---------------------------------------------------------------------------
# Subcommand: summary
# ---------------------------------------------------------------------------


class TestSummarySubcommand:
    def test_summary_concentration_warning(self, tmp_path):
        # Position taking >10% of account
        run_add(
            make_args(
                symbol="VIC",
                exchange="hose",
                shares=3300,
                avg_price=45000.0,
                buy_date="2026-05-04",
                sector="Bất động sản",
                state_dir=str(tmp_path),
            )
        )
        result = run_summary(
            make_args(
                prices="VIC:46500",
                state_dir=str(tmp_path),
                account_size=1_000_000_000,
                max_position_pct=10.0,
                max_sector_pct=30.0,
            )
        )
        # market_value = 153,450,000; NAV 1B → 15.345% > 10%
        assert any("VIC" in w for w in result["concentration_warnings"])

    def test_summary_sector_breakdown(self, tmp_path):
        run_add(
            make_args(
                symbol="VIC",
                exchange="hose",
                shares=1000,
                avg_price=45000.0,
                buy_date="2026-05-04",
                sector="Bất động sản",
                state_dir=str(tmp_path),
            )
        )
        run_add(
            make_args(
                symbol="HPG",
                exchange="hose",
                shares=1000,
                avg_price=28000.0,
                buy_date="2026-05-06",
                sector="Vật liệu",
                state_dir=str(tmp_path),
            )
        )
        result = run_summary(
            make_args(
                prices="VIC:45000,HPG:28000",
                state_dir=str(tmp_path),
                account_size=None,
                max_position_pct=None,
                max_sector_pct=None,
            )
        )
        assert "Bất động sản" in result["sector_breakdown_vnd"]
        assert "Vật liệu" in result["sector_breakdown_vnd"]
        assert result["sector_breakdown_vnd"]["Bất động sản"] == 45_000_000

    def test_summary_cash_calculation(self, tmp_path):
        run_add(
            make_args(
                symbol="VIC",
                exchange="hose",
                shares=1000,
                avg_price=45000.0,
                buy_date="2026-05-04",
                state_dir=str(tmp_path),
            )
        )
        result = run_summary(
            make_args(
                prices="VIC:45000",
                state_dir=str(tmp_path),
                account_size=100_000_000,
                max_position_pct=None,
                max_sector_pct=None,
            )
        )
        # NAV 100M, MV 45M → cash = 55M
        assert result["cash_vnd"] == 55_000_000
