---
name: vn-vcp-screener
description: Sàng lọc cổ phiếu Việt Nam theo mô hình VCP (Volatility Contraction Pattern) của Mark Minervini, hiệu chỉnh cho biên độ ±7% HOSE. Phát hiện các đợt contraction liên tiếp với range thu hẹp dần, volume giảm dần. Yêu cầu OHLCV ít nhất 60 phiên từ vn-data-fetcher. Kích hoạt khi user hỏi "tìm mã VCP", "stock đang siết biên độ", "breakout candidate kiểu Minervini" cho cổ phiếu VN. Vietnam VCP (Volatility Contraction Pattern) screener — Minervini-style pattern adapted for HOSE ±7% bands. Detects successive volatility contractions with declining volume.
---

# VN VCP Screener — Sàng lọc VCP cho cổ phiếu Việt Nam

## Tổng quan

VCP (Volatility Contraction Pattern) là mẫu hình breakout setup nổi tiếng của Mark Minervini. Skill này phát hiện VCP trong cổ phiếu Việt Nam, với các điều chỉnh quan trọng cho thị trường VN:

- **Biên độ ±7% HOSE** → định nghĩa "contraction tight" khác Mỹ
- **T+2.5 settlement** → không thể intraday flip; setup phải hold qua nhiều phiên
- **Lô 100** → position-sizing kết hợp với `vn-position-sizer`
- **Volume Bến đỉnh phải dry-up** (≥30% so với volume trung bình base)

VCP có 5 đặc trưng chính:
1. **Uptrend nền** — cổ phiếu đã trong uptrend (giá > MA50 > MA200)
2. **Multiple contractions** — ít nhất 2-3 đợt contraction (mỗi đợt là pullback rồi rally lại nhưng range hẹp hơn lần trước)
3. **Decreasing depth** — depth của mỗi contraction nhỏ hơn cái trước (T1 > T2 > T3)
4. **Volume dry-up** — volume giảm khi contraction (signs of consolidation)
5. **Pivot near recent high** — pivot point nằm trong 5-10% so với 52-week high

## Khi nào dùng

- Tìm breakout candidate cho swing 2-8 tuần
- Kết hợp với `vn-sector-analyst` (chọn ngành dẫn dắt) + `vn-foreign-room-tracker` (room hot) → high-quality setup
- Trong uptrend rõ ràng (`vn-sector-analyst` regime note = positive)
- **KHÔNG** dùng khi market đang downtrend rõ (FTD chưa confirm hoặc index dưới MA50)

## Điều kiện tiên quyết

- Python 3.9+ với `pandas` (kèm trong `[vn]` extras)
- OHLCV ≥60 phiên cho mỗi mã (lấy từ `vn-data-fetcher`)
- Tham chiếu: `references/vn_vcp_methodology.md`

## Workflow

### Bước 1: Lấy OHLCV cho universe

```bash
python skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VCB,BID,CTG,VIC,VHM,HPG,FPT,MWG,VNM,SSI,VCI,GAS,PLX \
  --start 2026-01-01 --end 2026-05-13 \
  --output-dir reports/
```

### Bước 2: Chạy screener

```bash
# Single-symbol mode
python skills/vn-vcp-screener/scripts/vn_vcp_screener.py \
  --ohlcv-file reports/vn_ohlcv_VIC_*.json \
  --output-dir reports/

# Batch mode (consumes multi-symbol JSON)
python skills/vn-vcp-screener/scripts/vn_vcp_screener.py \
  --ohlcv-glob 'reports/vn_ohlcv_*2026-05-13*.json' \
  --min-contractions 2 \
  --max-contractions 5 \
  --output-dir reports/
```

### Bước 3: Đọc output

Output JSON gồm:

- **Mỗi mã có VCP detected**: pivot price, stop price gợi ý, contractions detail
- **Score 0-100**: tổng hợp 5 tiêu chí
- **Grade A/B/C**: A = đầy đủ tất cả 5 đặc trưng, B = 4/5, C = 3/5
- **Rejection reasons**: nếu không qua, lý do cụ thể

### Bước 4: Combine với context

```bash
# Lấy top 3 từ VCP output, build trade plan
python skills/vn-breakout-trade-planner/scripts/vn_breakout_planner.py \
  --account-size 1000000000 \
  --symbol <từ VCP output> \
  --pivot <pivot từ VCP> --stop <stop từ VCP> \
  --risk-pct 1.0 \
  --sector-analysis-file reports/vn_sector_*.json \
  --foreign-room-file reports/vn_foreign_room_*.json \
  --output-dir reports/
```

## Tiêu chí scoring (5 components)

| Component | Weight | Pass criteria |
| --- | --- | --- |
| **Uptrend** | 25 | Giá > MA50 > MA200; MA50 đang dốc lên |
| **Contractions** | 25 | ≥2 contractions với depth giảm dần |
| **Volume dry-up** | 20 | Volume ở đáy contraction ≤70% MA50 volume |
| **Pivot quality** | 15 | Pivot trong 10% của 52-week high |
| **Wide-and-loose check** | 15 | Range tổng base ≤25%; nếu >25% → cap grade |

### Grade interpretation

- **A (80-100):** Setup A+; full 5 tiêu chí; sẵn sàng đặt lệnh pivot
- **B (60-79):** Setup tốt, 1 tiêu chí yếu; cân nhắc giảm size 50%
- **C (40-59):** Setup yếu; monitor, không đặt lệnh
- **<40:** Reject, không phải VCP

## Output Format

```json
{
  "schema_version": "1.0",
  "as_of": "2026-05-13T10:00:00+07:00",
  "universe_size": 13,
  "candidates_count": 3,
  "rejected_count": 10,
  "windows": {"trend": 50, "long_trend": 200, "volume_avg": 50},
  "candidates": [
    {
      "symbol": "FPT",
      "exchange": "hose",
      "grade": "A",
      "score": 85,
      "components": {
        "uptrend": 25,
        "contractions": 22,
        "volume_dryup": 18,
        "pivot_quality": 12,
        "wide_loose_penalty": 8
      },
      "pivot_price": 142000,
      "suggested_stop": 135000,
      "stop_pct": 4.93,
      "contractions": [
        {"index": 1, "depth_pct": 12.5, "duration_days": 18},
        {"index": 2, "depth_pct": 7.8, "duration_days": 12},
        {"index": 3, "depth_pct": 4.2, "duration_days": 8}
      ],
      "base_total_range_pct": 18.2,
      "pivot_to_52w_high_pct": 3.5,
      "volume_at_pivot_vs_ma50": 0.65,
      "trend_signal": "strong",
      "notes": ["3 contractions detected", "Volume dry-up confirmed"]
    }
  ],
  "rejected": [
    {
      "symbol": "VIC",
      "score": 35,
      "rejection_reasons": [
        "Wide-and-loose: base range 32% > 25% threshold",
        "Only 1 contraction detected (min 2 required)"
      ]
    }
  ]
}
```

## Resources

- `references/vn_vcp_methodology.md` — Full VCP detection logic + VN adjustments
- `scripts/vn_vcp_screener.py` — Main screener
- Cross-references:
  - `skills/vn-data-fetcher/` — OHLCV input
  - `skills/vn-breakout-trade-planner/` — Trade plan from VCP output
  - `skills/vn-sector-analyst/` — Sector context filter

## Nguyên tắc

1. **VCP là setup, không phải tín hiệu mua** — Detection chỉ là bước 1. Vẫn cần xác nhận trend + sector + risk management.
2. **Biên độ ±7% thay đổi định nghĩa "tight"** — Một contraction 5% ở VN tương đương 7-10% ở Mỹ về đặc trưng "tight". Methodology điều chỉnh cho phù hợp.
3. **Volume dry-up là tiêu chí cứng** — Không có volume contraction → không phải VCP, dù price action đẹp.
4. **Wide-and-loose = không VCP** — Nếu base range > 25%, cap grade ở B. >35% reject hoàn toàn.
5. **Reqs OHLCV daily** — Skill này không work với intraday data. Cần ≥60 phiên 1D.
