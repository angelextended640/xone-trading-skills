# VN Earnings Analyzer — Phương pháp luận

## Mục tiêu

Sau mỗi mùa BCTC, scan các báo cáo gần đây để xác định cổ phiếu có **phản ứng giá mạnh kèm chất lượng kỹ thuật tốt** — ứng viên cho PEAD (post-earnings announcement drift) setup tiếp theo.

## Bốn cửa sổ KQKD chính tại VN (2026)

| Quý | Deadline báo cáo | Window công bố tập trung | Sự kiện mặt bằng giao dịch |
| --- | --- | --- | --- |
| Q4 (năm trước) | 31/01 | **Mid Jan – Feb** | Nhiều mã có audited annual report → wash-sale buying |
| Q1 | 30/04 | **Late Apr** | Sau Tết, dòng tiền retail quay lại |
| Q2 (bán niên) | 31/08 (cần soát xét) | **Late Jul – early Aug + cuối Aug** | Hai đợt: tự công bố cuối Jul, soát xét cuối Aug |
| Q3 | 30/10 | **Late Oct – early Nov** | Pre-Tết position building |

→ Skill này hữu ích nhất khi chạy trong các window trên hoặc 1-2 tuần sau.

## 5 yếu tố chấm điểm (mỗi yếu tố +1 điểm, tổng tối đa 5)

| Yếu tố | Ngưỡng VN | Lý do |
| --- | --- | --- |
| **Gap size** | `gap_pct ≥ 2.0` | VN bị cap bởi biên độ ±7% → gap 2-3% đã là tín hiệu mạnh (US thường yêu cầu ≥5%) |
| **Volume** | `volume_relative ≥ 1.5` | Volume = 1.5× trung bình 20 phiên thể hiện sự quan tâm |
| **Pre-earnings 20D trend** | `trend_20d_pct ≥ 0` | Up-trend trước báo cáo + báo cáo positive = momentum kép |
| **MA50/MA200 position** | `above_ma50 AND above_ma200` | Long-term trend intact |
| **EPS surprise** | `eps_surprise_pct > 0` | Beat estimate — báo cáo "tốt hơn dự kiến" |

## Calibration VN-specific

- **Gap 2%** thấp hơn US (5-10%) vì biên độ ±7%/phiên cap tối đa: nếu công ty beat lớn, giá vẫn chỉ tăng được 7% trong ngày → gap 2-4% trong giờ ATO/ATC đã là tín hiệu rất mạnh
- **Volume relative 1.5×** tương đồng US — không cần điều chỉnh
- **Trend lookback 20D** tương đương 1 tháng phiên giao dịch (~22 phiên giao dịch) — đủ smoothing
- **EPS surprise**: không có consensus estimate public ở VN; thay vào đó so sánh với cùng kỳ năm trước (YoY) hoặc quý trước (QoQ). Trường `eps_surprise_pct` user phải tự tính, mặc định = QoQ growth

## Grade

| Score | Grade |
| --- | --- |
| 5 | A — Báo cáo + phản ứng tuyệt vời, ưu tiên PEAD watchlist |
| 4 | B — Phản ứng tốt, monitor 1 yếu tố yếu |
| 3 | C — Trung bình |
| 2 | D — Yếu, có rủi ro |
| 0-1 | F — Loại |

## Source dữ liệu

```bash
# Lấy fundamentals theo quarter (gồm report_date + EPS)
python skills/vn-data-fetcher/scripts/vn_data_fetcher.py fundamentals \
  --symbols FPT,VIC,HPG,MWG --period quarter

# Lấy OHLCV cho 30 phiên quanh ngày báo cáo (tính gap, volume, MA)
python skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols FPT,VIC,HPG,MWG \
  --start 2026-03-01 --end 2026-05-13
```

User (hoặc Claude) tổng hợp thành earnings.json:

```json
[
  {
    "symbol": "FPT",
    "report_date": "2026-04-25",
    "gap_pct": 2.5,
    "volume_relative": 1.6,
    "trend_20d_pct": 5.0,
    "above_ma50": true,
    "above_ma200": true,
    "eps_surprise_pct": 10.0,
    "has_red_candle_pullback": true,
    "current_price": 142000,
    "report_day_low": 138000,
    "status": "Normal"
  }
]
```

Trường `status` tuỳ chọn — nếu Kiểm soát/Hạn chế/Tạm ngừng/Cảnh báo, skill mặc định skip (trừ khi `--include-flagged`).

## Tham chiếu vn-market-mechanics

- [`vn_trading_rules.md`](../../vn-market-mechanics/references/vn_trading_rules.md) — sessions (gap = open vs prev_close), status flags
- [`vn_price_limits_orders.md`](../../vn-market-mechanics/references/vn_price_limits_orders.md) — biên độ ±7%/10%/15% cap gap size
- [`vn_fees_and_taxes.md`](../../vn-market-mechanics/references/vn_fees_and_taxes.md) — round-trip cost ~0.4% → break-even threshold cho PEAD pipeline (vn-pead-screener)
- [`vn_data_sources.md`](../../vn-market-mechanics/references/vn_data_sources.md) — vnstock fundamentals endpoint

## Lưu ý áp dụng

- Skill này **đánh giá**, không phải **lựa chọn entry**. Output là grade; entry plan + ceiling/floor + stop là việc của `vn-pead-screener` (Mode B pipeline).
- Khi gap > biên độ (rare): coi như `gap_pct = ±band%` (cap). VN tự động cap nên data từ vnstock đã chính xác.
- Sau Tết và sau Q4 audit, có thể có "wash" — báo cáo Q4 sai lệch so với Q3 unaudited → false-positive grade A. Lọc thêm bằng `vn-news-analyst` đọc tin "audit adjustment".
