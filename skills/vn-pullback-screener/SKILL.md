---
name: vn-pullback-screener
description: Sàng lọc cổ phiếu Việt Nam đang pullback đẹp trong uptrend. Tìm mã giá điều chỉnh về MA20/MA50, RSI giảm về 35-50, nhưng vẫn giữ trên MA200 và uptrend dài hạn. Yêu cầu OHLCV 200+ phiên từ vn-data-fetcher. Kích hoạt khi user hỏi "tìm mã pullback", "cổ phiếu test MA20/MA50", "cổ phiếu test hỗ trợ", "buy the dip" cho cổ phiếu VN. Vietnam pullback screener — uptrending stocks pulling back to MA20 / MA50 with RSI 35-50, still above MA200. Lower-risk swing entry than breakout buying.
---

# VN Pullback Screener — Sàng lọc mã pullback trong uptrend

## Tổng quan

Tìm cổ phiếu **đang trong uptrend rõ ràng** nhưng **vừa pullback** về vùng hỗ trợ động (MA20 hoặc MA50). Đây là entry style ít rủi ro hơn breakout vì:

- Giá đã ở **xa hơn** điểm phá trần / sàn → setup chưa muộn
- Stop **gần hơn** (just below MA50 hoặc gần đáy pullback) → R-multiple tốt hơn
- Phù hợp với **T+2.5** vì không cần intraday timing (chờ vài phiên xác nhận hỗ trợ)

5 tiêu chí pullback:
1. **Trend dài hạn còn nguyên** — Price > MA200, MA50 > MA200, MA200 dốc lên
2. **Pullback từ đỉnh gần** — Giá đã giảm 3-12% từ đỉnh 20 phiên
3. **Test hỗ trợ động** — Giá touch / gần MA20 hoặc MA50
4. **RSI vào vùng oversold lành mạnh** — RSI(14) trong khoảng 35-50
5. **Volume pullback dry-up** — Volume tại đáy pullback < volume MA50

## Khi nào dùng

- Tìm entry an toàn sau breakout / VCP đã chạy → đón cú test hỗ trợ
- Trong market regime tích cực (`vn-sector-analyst` regime note = positive)
- Pair với `vn-sector-analyst` để chọn pullback trong ngành dẫn dắt
- **KHÔNG** dùng khi market đang downtrend mạnh — pullback có thể là "broken trend"

## Điều kiện tiên quyết

- Python 3.9+
- OHLCV ≥200 phiên (cần đủ tính MA200)
- Tham chiếu: `references/vn_pullback_methodology.md`

## Workflow

```bash
# 1. Fetch OHLCV cho universe
python skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VCB,BID,VIC,VHM,HPG,FPT,MWG,VNM,SSI,GAS \
  --start 2025-07-01 --end 2026-05-13 \
  --output-dir reports/

# 2. Chạy pullback screener
python skills/vn-pullback-screener/scripts/vn_pullback_screener.py \
  --ohlcv-glob 'reports/vn_ohlcv_*2026-05-13*.json' \
  --min-pullback-pct 3 --max-pullback-pct 12 \
  --rsi-low 35 --rsi-high 50 \
  --output-dir reports/

# 3. Top candidates → build trade plan
python skills/vn-breakout-trade-planner/scripts/vn_breakout_planner.py \
  --account-size 1000000000 \
  --symbol <top candidate> \
  --pivot <pivot from pullback output> \
  --stop <stop suggested> \
  --setup-type pullback \
  --risk-pct 1.0 \
  --output-dir reports/
```

## Tiêu chí scoring (5 components)

| Component | Weight | Pass criteria |
| --- | --- | --- |
| **Long-term uptrend** | 25 | Price > MA200, MA50 > MA200, MA200 rising |
| **Pullback magnitude** | 20 | -3% to -12% from 20-day high |
| **Support test (MA20/MA50)** | 20 | Distance to MA20 < 3% OR distance to MA50 < 5% |
| **RSI sweet spot** | 20 | RSI(14) in 35-50 range |
| **Volume pullback dry-up** | 15 | Volume at low / MA50 vol ≤ 0.85 |

### Grade

- **A (80-100):** All 5 criteria met; ideal pullback entry
- **B (60-79):** 4/5 criteria; viable but reduce size
- **C (40-59):** Setup weakening; monitor only
- **<40:** Reject

## Output Format

```json
{
  "schema_version": "1.0",
  "as_of": "2026-05-13T10:00:00+07:00",
  "universe_size": 10,
  "candidates_count": 3,
  "candidates": [
    {
      "symbol": "FPT",
      "exchange": "hose",
      "grade": "A",
      "score": 88,
      "components": {
        "long_term_uptrend": 25,
        "pullback_magnitude": 18,
        "support_test": 20,
        "rsi_sweet_spot": 17,
        "volume_dryup": 8
      },
      "current_price": 138500,
      "high_20d": 145000,
      "pullback_pct": -4.48,
      "ma20": 139800,
      "ma50": 136200,
      "ma200": 122500,
      "distance_to_ma20_pct": -0.93,
      "distance_to_ma50_pct": 1.69,
      "rsi_14": 42.3,
      "volume_ratio_low_vs_ma50": 0.72,
      "ma200_slope_pct_per_month": 1.8,
      "suggested_entry": 139000,
      "suggested_stop": 132000,
      "stop_pct": 5.04,
      "notes": ["Testing MA20 support", "RSI in healthy oversold zone"]
    }
  ],
  "rejected": [
    {
      "symbol": "VIC",
      "score": 30,
      "rejection_reasons": ["RSI 62 (above 50 — not in pullback)"]
    }
  ]
}
```

## Resources

- `references/vn_pullback_methodology.md` — Full methodology
- `scripts/vn_pullback_screener.py` — Main script

## Nguyên tắc

1. **Pullback ≠ Reversal** — Tránh mã đang phá MA200 hoặc MA50 dốc xuống. Đó là reversal, không phải pullback.
2. **RSI 35-50 là "sweet spot"** — Dưới 35 quá oversold (có thể là free-fall); trên 50 không phải pullback nữa.
3. **Volume dry-up xác nhận** — Pullback healthy: volume giảm. Pullback xấu: volume tăng (distribution).
4. **Combine với sector signal** — Pullback trong ngành đang weak ít khi recover. Lọc qua `vn-sector-analyst`.
5. **Stop dưới MA50** — Stop hợp lý: tại đáy pullback × 0.97 HOẶC MA50 × 0.97 (whichever is lower)
