"""Tests for VN position sizer."""

import pytest

from vn_position_sizer import (
    LOT_SIZE,
    VnSizingParameters,
    apply_constraints,
    calculate_atr_based,
    calculate_fixed_fractional,
    calculate_kelly,
    calculate_position,
    compute_price_band,
    estimate_fees_and_taxes,
    round_to_lot,
    round_to_tick,
    tick_size,
    validate_parameters,
)


# ----------------------------------------------------------------------------
# Tick size & rounding
# ----------------------------------------------------------------------------


class TestTickSize:
    def test_hose_below_10k(self):
        assert tick_size("hose", 5000) == 10
        assert tick_size("hose", 9990) == 10

    def test_hose_10k_to_50k(self):
        assert tick_size("hose", 10_000) == 50
        assert tick_size("hose", 25_000) == 50
        assert tick_size("hose", 49_950) == 50

    def test_hose_above_50k(self):
        assert tick_size("hose", 50_000) == 100
        assert tick_size("hose", 145_000) == 100

    def test_hnx_uniform(self):
        assert tick_size("hnx", 5_000) == 100
        assert tick_size("hnx", 50_000) == 100

    def test_upcom_uniform(self):
        assert tick_size("upcom", 5_000) == 100


class TestRoundToTick:
    def test_round_nearest_hose_45k(self):
        # tick = 50 at 45,000 (range 10k-50k)
        assert round_to_tick(45_237, "hose") == 45_250
        assert round_to_tick(45_220, "hose") == 45_200

    def test_round_down_hose(self):
        # 45,299, tick 50 → floor = 45,250
        assert round_to_tick(45_299, "hose", mode="down") == 45_250

    def test_round_up_hose(self):
        # 45,201, tick 50 → ceil = 45,250
        assert round_to_tick(45_201, "hose", mode="up") == 45_250

    def test_round_at_100_tick_band(self):
        # tick = 100 at >= 50,000
        assert round_to_tick(55_237, "hose", mode="down") == 55_200
        assert round_to_tick(55_237, "hose", mode="up") == 55_300

    def test_round_to_50_band(self):
        # tick = 50 in 10k-50k range
        assert round_to_tick(28_437, "hose", mode="down") == 28_400
        assert round_to_tick(28_437, "hose", mode="up") == 28_450


class TestRoundToLot:
    def test_basic(self):
        assert round_to_lot(3333, 100) == 3300
        assert round_to_lot(99, 100) == 0
        assert round_to_lot(100, 100) == 100

    def test_alternate_lot(self):
        assert round_to_lot(13, 10) == 10


# ----------------------------------------------------------------------------
# Price band
# ----------------------------------------------------------------------------


class TestPriceBand:
    def test_hose_band(self):
        band = compute_price_band(45_000, "hose")
        # 45,000 × 1.07 = 48,150. Price in 10k-50k range → tick 50. 48,150 / 50 = 963 (exact on tick).
        # 45,000 × 0.93 = 41,850. Tick 50. 41,850 / 50 = 837 (exact on tick).
        assert band["price_band_pct"] == 7.0
        assert band["reference_price"] == 45_000
        assert band["ceiling_price"] == 48_150
        assert band["floor_price"] == 41_850

    def test_hose_band_below_10k(self):
        # 5,000 VND, tick = 10 below 10k
        band = compute_price_band(5_000, "hose")
        # raw_ceiling = 5,350, tick=10 → round down = 5,350
        # raw_floor = 4,650, tick=10 → round up = 4,650
        assert band["ceiling_price"] == 5_350
        assert band["floor_price"] == 4_650

    def test_hnx_band(self):
        band = compute_price_band(20_000, "hnx")
        # ±10%, tick = 100 uniform
        # raw_ceiling = 22,000 → 22,000
        # raw_floor = 18,000 → 18,000
        assert band["price_band_pct"] == 10.0
        assert band["ceiling_price"] == 22_000
        assert band["floor_price"] == 18_000

    def test_upcom_band(self):
        band = compute_price_band(15_000, "upcom")
        # ±15%, tick = 100
        # raw_ceiling = 17,250 → round down = 17,200
        # raw_floor = 12,750 → round up = 12,800
        assert band["price_band_pct"] == 15.0
        assert band["ceiling_price"] == 17_200
        assert band["floor_price"] == 12_800


# ----------------------------------------------------------------------------
# Fixed Fractional
# ----------------------------------------------------------------------------


class TestFixedFractional:
    def test_basic_vic_example(self):
        """VIC: 1B VND, entry 45k, stop 42k, risk 1% → 3,300 shares."""
        params = VnSizingParameters(
            account_size_vnd=1_000_000_000,
            entry_price=45_000,
            stop_price=42_000,
            risk_pct=1.0,
        )
        result = calculate_fixed_fractional(params)
        assert result["raw_shares"] == 3333
        assert result["lot_rounded_shares"] == 3300
        assert result["risk_per_share_vnd"] == 3000
        assert result["target_dollar_risk_vnd"] == 10_000_000
        assert result["actual_dollar_risk_vnd"] == 9_900_000  # 3300 * 3000

    def test_lot_rounds_down_never_up(self):
        """Verify shares always round DOWN to lot (never up)."""
        params = VnSizingParameters(
            account_size_vnd=1_000_000_000,
            entry_price=45_000,
            stop_price=42_000,
            risk_pct=1.0,
        )
        result = calculate_fixed_fractional(params)
        assert result["lot_rounded_shares"] <= result["raw_shares"]
        assert result["lot_rounded_shares"] % LOT_SIZE == 0


# ----------------------------------------------------------------------------
# ATR-based
# ----------------------------------------------------------------------------


class TestAtrBased:
    def test_hpg_example(self):
        """HPG: 500M VND, entry 28k, ATR 800, mult 2, risk 1%."""
        params = VnSizingParameters(
            account_size_vnd=500_000_000,
            exchange="hose",
            entry_price=28_000,
            atr=800,
            atr_multiplier=2.0,
            risk_pct=1.0,
        )
        result = calculate_atr_based(params)
        # stop_distance = 1,600 → stop_raw = 26,400 → tick 50 down → 26,400
        assert result["stop_price"] == 26_400
        # risk per share = 1,600; budget = 5M; raw_shares = 3,125
        # lot rounded down: 3,100
        assert result["raw_shares"] == 3_125
        assert result["lot_rounded_shares"] == 3_100


# ----------------------------------------------------------------------------
# Kelly
# ----------------------------------------------------------------------------


class TestKelly:
    def test_positive_expectancy(self):
        params = VnSizingParameters(
            account_size_vnd=1_000_000_000,
            win_rate=0.55,
            avg_win=2.5,
            avg_loss=1.0,
        )
        result = calculate_kelly(params)
        # Kelly = 0.55 - 0.45/2.5 = 0.55 - 0.18 = 0.37 = 37%
        # Half = 18.5%
        assert result["kelly_pct"] == 37.0
        assert result["half_kelly_pct"] == 18.5

    def test_negative_expectancy_floors_at_zero(self):
        """Negative-EV system: Kelly should floor at 0."""
        params = VnSizingParameters(
            account_size_vnd=1_000_000_000,
            win_rate=0.30,
            avg_win=1.0,
            avg_loss=1.0,
        )
        result = calculate_kelly(params)
        # 0.30 - 0.70/1.0 = -0.40 → floored to 0
        assert result["kelly_pct"] == 0
        assert result["half_kelly_pct"] == 0


# ----------------------------------------------------------------------------
# Fees and taxes
# ----------------------------------------------------------------------------


class TestFeesAndTaxes:
    def test_vic_round_trip(self):
        """3300 VIC @ 45k, fee 0.15%, tax 0.1% → round-trip cost = 0.4%."""
        params = VnSizingParameters(
            account_size_vnd=1_000_000_000,
            broker_fee_pct=0.15,
            sale_tax_pct=0.10,
        )
        fees = estimate_fees_and_taxes(3300, 45_000, params)
        # Position = 148,500,000
        # buy_fee = 0.15% × 148.5M = 222,750
        # sell_fee = 222,750
        # sell_tax = 0.10% × 148.5M = 148,500
        # total = 594,000 (0.40%)
        assert fees["buy_fee_vnd"] == 222_750
        assert fees["sell_fee_vnd_at_entry"] == 222_750
        assert fees["sell_tax_vnd_at_entry"] == 148_500
        assert fees["round_trip_cost_vnd"] == 594_000
        assert fees["round_trip_cost_pct"] == 0.4

    def test_zero_shares_pct_zero(self):
        params = VnSizingParameters(account_size_vnd=1_000_000_000)
        fees = estimate_fees_and_taxes(0, 45_000, params)
        assert fees["round_trip_cost_vnd"] == 0
        assert fees["round_trip_cost_pct"] == 0


# ----------------------------------------------------------------------------
# Constraints
# ----------------------------------------------------------------------------


class TestConstraints:
    def test_max_position_binding(self):
        """If max_position_pct is tighter than risk-based, it binds and rounds to lot."""
        params = VnSizingParameters(
            account_size_vnd=1_000_000_000,
            entry_price=45_000,
            stop_price=42_000,
            risk_pct=1.0,
            max_position_pct=5.0,  # 50M / 45k = 1,111 shares → lot 1,100
        )
        # risk_based = 3,300 shares; max_position = 1,100 shares
        final, constraints, binding = apply_constraints(3300, params)
        assert final == 1_100
        assert binding == "max_position_pct"
        assert any(c.get("binding") for c in constraints)

    def test_max_sector_binding(self):
        params = VnSizingParameters(
            account_size_vnd=1_000_000_000,
            entry_price=45_000,
            stop_price=42_000,
            risk_pct=1.0,
            max_sector_pct=20.0,
            current_sector_exposure=18.0,  # 2% remaining = 20M / 45k = 444 → 400
        )
        final, constraints, binding = apply_constraints(3300, params)
        assert final == 400
        assert binding == "max_sector_pct"

    def test_no_constraints_passes_through(self):
        params = VnSizingParameters(
            account_size_vnd=1_000_000_000,
            entry_price=45_000,
            stop_price=42_000,
            risk_pct=1.0,
        )
        final, constraints, binding = apply_constraints(3300, params)
        assert final == 3_300
        assert binding is None


# ----------------------------------------------------------------------------
# End-to-end via calculate_position
# ----------------------------------------------------------------------------


class TestCalculatePosition:
    def test_e2e_vic_long(self):
        params = VnSizingParameters(
            account_size_vnd=1_000_000_000,
            exchange="hose",
            symbol="VIC",
            entry_price=45_000,
            stop_price=42_000,
            risk_pct=1.0,
        )
        result = calculate_position(params)
        assert result["market"] == "vn"
        assert result["exchange"] == "hose"
        assert result["symbol"] == "VIC"
        assert result["mode"] == "shares"
        assert result["final_recommended_shares"] == 3_300
        assert result["final_position_value_vnd"] == 148_500_000
        assert result["final_risk_vnd"] == 9_900_000
        assert result["final_risk_pct"] == 0.99
        assert result["binding_constraint"] is None
        assert "settlement_note" in result
        # No warning because stop > floor
        assert "warnings" not in result or not result["warnings"]

    def test_e2e_warns_when_stop_below_floor(self):
        # HPG 28k, stop 25,500 below floor 26,050
        params = VnSizingParameters(
            account_size_vnd=500_000_000,
            exchange="hose",
            symbol="HPG",
            entry_price=28_000,
            stop_price=25_500,
            risk_pct=1.0,
        )
        result = calculate_position(params)
        assert result["vn_market_context"]["stop_below_floor"] is True
        assert "warnings" in result
        assert any("sàn" in w for w in result["warnings"])

    def test_e2e_kelly_budget_mode(self):
        params = VnSizingParameters(
            account_size_vnd=1_000_000_000,
            win_rate=0.55,
            avg_win=2.5,
            avg_loss=1.0,
        )
        result = calculate_position(params)
        assert result["mode"] == "budget"
        # Half-kelly 18.5% of 1B = 185M
        assert result["recommended_risk_budget_vnd"] == 185_000_000
        assert result["recommended_risk_budget_pct"] == 18.5

    def test_e2e_hnx_band(self):
        params = VnSizingParameters(
            account_size_vnd=500_000_000,
            exchange="hnx",
            symbol="SHS",
            entry_price=18_000,
            stop_price=16_500,
            risk_pct=1.0,
        )
        result = calculate_position(params)
        assert result["vn_market_context"]["price_band_pct"] == 10.0
        # 18k × 0.9 = 16,200 → floor at tick 100
        assert result["vn_market_context"]["floor_price"] == 16_200
        # Stop 16,500 > floor 16,200, no warning
        assert result["vn_market_context"]["stop_below_floor"] is False

    def test_e2e_includes_fees(self):
        params = VnSizingParameters(
            account_size_vnd=1_000_000_000,
            exchange="hose",
            symbol="VIC",
            entry_price=45_000,
            stop_price=42_000,
            risk_pct=1.0,
        )
        result = calculate_position(params)
        fees = result["fees_and_taxes_estimate"]
        assert fees["round_trip_cost_pct"] == 0.4


# ----------------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------------


class TestValidation:
    def test_negative_account_rejected(self):
        params = VnSizingParameters(account_size_vnd=-100_000)
        with pytest.raises(ValueError, match="account_size"):
            validate_parameters(params)

    def test_stop_above_entry_rejected(self):
        params = VnSizingParameters(
            account_size_vnd=1_000_000_000,
            entry_price=45_000,
            stop_price=46_000,  # invalid for long
        )
        with pytest.raises(ValueError, match="stop_price"):
            validate_parameters(params)

    def test_bad_exchange_rejected(self):
        params = VnSizingParameters(
            account_size_vnd=1_000_000_000,
            exchange="nyse",
        )
        with pytest.raises(ValueError, match="exchange"):
            validate_parameters(params)

    def test_invalid_win_rate_rejected(self):
        params = VnSizingParameters(
            account_size_vnd=1_000_000_000,
            win_rate=1.5,
            avg_win=1.0,
            avg_loss=1.0,
        )
        with pytest.raises(ValueError, match="win_rate"):
            validate_parameters(params)
