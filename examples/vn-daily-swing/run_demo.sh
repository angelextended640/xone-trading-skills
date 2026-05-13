#!/usr/bin/env bash
#
# VN Daily Swing — offline runnable demo.
#
# Demonstrates the deterministic vn-* skills that don't need network access:
#   1. vn-foreign-room-tracker  (record + report two days of room data)
#   2. vn-position-sizer        (size the trade)
#   3. vn-breakout-trade-planner (full trade plan with VN guardrails)
#   4. vn-tax-fee-calculator    (cost + broker comparison)
#   5. vn-portfolio-manager     (record the trade)
#
# Skipped (require network / live data):
#   - vn-data-fetcher / vn-sector-analyst   (run separately with vnstock)
#   - vn-news-analyst                       (WebSearch / WebFetch tools)
#
# Usage:
#   bash examples/vn-daily-swing/run_demo.sh
#

set -euo pipefail

DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$DEMO_DIR/../.." && pwd)"
WORK_DIR="$(mktemp -d)"

echo "==> Demo work dir: $WORK_DIR"
mkdir -p "$WORK_DIR/reports" "$WORK_DIR/state/vn_foreign_room" "$WORK_DIR/state/vn_portfolio"

cd "$REPO_ROOT"

echo ""
echo "==========================================================="
echo "  Step 1: Record yesterday's and today's foreign-room data"
echo "==========================================================="
python3 skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py record \
  --input "$DEMO_DIR/sample_inputs/yesterday_room.csv" \
  --as-of 2026-05-12 \
  --state-dir "$WORK_DIR/state/vn_foreign_room" \
  --output-dir "$WORK_DIR/reports" 2>&1 | tail -3

python3 skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py record \
  --input "$DEMO_DIR/sample_inputs/today_room.csv" \
  --as-of 2026-05-13 \
  --state-dir "$WORK_DIR/state/vn_foreign_room" \
  --output-dir "$WORK_DIR/reports" 2>&1 | tail -3

echo ""
echo "==========================================================="
echo "  Step 2: Report on foreign-room changes"
echo "==========================================================="
python3 skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py report \
  --state-dir "$WORK_DIR/state/vn_foreign_room" \
  --lookback-days 1 \
  --full-threshold 99 --release-threshold 90 --spike-threshold 0.5 \
  --output-dir "$WORK_DIR/reports" 2>&1 | tail -15

echo ""
echo "==========================================================="
echo "  Step 3: Size the trade — FPT at 142,000, stop 135,000"
echo "==========================================================="
python3 skills/vn-position-sizer/scripts/vn_position_sizer.py \
  --account-size 1000000000 \
  --symbol FPT --exchange hose \
  --entry 142000 --stop 135000 \
  --risk-pct 1.0 \
  --max-position-pct 10 --max-sector-pct 30 \
  --sector "Cong nghe" --current-sector-exposure 0 \
  --output-dir "$WORK_DIR/reports" 2>&1 | tail -15

echo ""
echo "==========================================================="
echo "  Step 4: Build full trade plan with VN guardrails"
echo "==========================================================="
python3 skills/vn-breakout-trade-planner/scripts/vn_breakout_planner.py \
  --account-size 1000000000 \
  --symbol FPT --exchange hose \
  --setup-type breakout \
  --pivot 142000 --stop 135000 --risk-pct 1.0 \
  --buy-date 2026-05-13 \
  --foreign-room-file "$WORK_DIR/reports"/vn_foreign_room_report_*.json \
  --output-dir "$WORK_DIR/reports" 2>&1 | tail -20

echo ""
echo "==========================================================="
echo "  Step 5: Compare broker costs for this trade"
echo "==========================================================="
python3 skills/vn-tax-fee-calculator/scripts/vn_tax_fee_calculator.py compare \
  --shares 700 --entry 142000 --exit 149000 \
  --brokers vps,ssi,tcbs,dnse \
  --output-dir "$WORK_DIR/reports" 2>&1 | tail -10

echo ""
echo "==========================================================="
echo "  Step 6: Record the executed trade in the portfolio"
echo "==========================================================="
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py add \
  --symbol FPT --exchange hose \
  --shares 700 --avg-price 142000 \
  --buy-date 2026-05-13 --sector "Cong nghe" \
  --state-dir "$WORK_DIR/state/vn_portfolio" \
  --output-dir "$WORK_DIR/reports" 2>&1 | tail -3

echo ""
echo "==========================================================="
echo "  Step 7: End-of-day portfolio summary (FPT closes at 144,000)"
echo "==========================================================="
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py summary \
  --prices "FPT:144000" \
  --account-size 1000000000 \
  --max-position-pct 10 --max-sector-pct 30 \
  --state-dir "$WORK_DIR/state/vn_portfolio" \
  --output-dir "$WORK_DIR/reports" 2>&1 | tail -10

echo ""
echo "==========================================================="
echo "  Step 8: Run CANSLIM Screener"
echo "==========================================================="
python3 skills/vn-canslim-screener/scripts/vn_canslim_screener.py \
  --universe skills/vn-canslim-screener/references/sample_universe.json > "$WORK_DIR/reports/canslim_output.json"
cat "$WORK_DIR/reports/canslim_output.json" | tail -15

echo ""
echo "==========================================================="
echo "  Step 9: Run Earnings Analyzer & PEAD Screener"
echo "==========================================================="
python3 skills/vn-earnings-analyzer/scripts/vn_earnings_analyzer.py \
  --input "$DEMO_DIR/sample_inputs/sample_earnings.json" > "$WORK_DIR/reports/earnings_output.json"
python3 skills/vn-pead-screener/scripts/vn_pead_screener.py \
  --candidates "$WORK_DIR/reports/earnings_output.json" > "$WORK_DIR/reports/pead_output.json"
cat "$WORK_DIR/reports/pead_output.json" | tail -15

echo ""
echo "==========================================================="
echo "  Demo complete. Reports written to: $WORK_DIR/reports/"
echo "==========================================================="
ls -la "$WORK_DIR/reports" | tail -15
