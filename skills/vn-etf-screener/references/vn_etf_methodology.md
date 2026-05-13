# VN ETF Screener — Phương pháp luận

## Mục tiêu

Lọc các ETF đang niêm yết tại HOSE/HNX để chọn ra quỹ phù hợp làm **Core portfolio sleeve** (passive backbone) — chứ không phải để swing trade ETF.

## Universe ETF chính tại Việt Nam (2026-05)

| Ticker | Tên đầy đủ | Bench | Quản lý | Đặc điểm |
| --- | --- | --- | --- | --- |
| **E1VFVN30** | DCVFMVN30 ETF | VN30 | Dragon Capital | ETF VN30 lâu đời nhất, AUM lớn nhất |
| **FUEVFVND** | DCVFMVN Diamond ETF | VN Diamond | Dragon Capital | Tracking rổ Diamond — các blue-chip kín room ngoại |
| **FUESSV50** | SSIAM VNX50 ETF | VNX50 | SSIAM | Rổ rộng hơn VN30 |
| **FUESSV30** | SSIAM VN30 ETF | VN30 | SSIAM | Cạnh tranh với E1VFVN30 |
| **FUEVN100** | VinaCapital VN100 ETF | VN100 | VinaCapital | Rổ rộng nhất, top-100 vốn hóa HOSE |
| **FUEKIVFS** | KIM Growth VN30 ETF | VN30 | Kim VietNam Fund Management | ETF VN30 thứ ba |
| **FUEVFVND** | (lưu ý: trùng ký hiệu rút gọn — dùng tên đầy đủ khi báo cáo) | | | |

> Danh sách trên không phải universe đóng — khi có ETF mới niêm yết, bổ sung vào `references/vn_etf_list.json`.

## Cấu trúc Universe JSON

```json
[
  {
    "symbol": "E1VFVN30",
    "name": "DCVFMVN30 ETF",
    "nav_per_share": 21500,
    "market_price": 21600,
    "tracking_error_pct": 0.8,
    "expense_ratio_pct": 0.65,
    "volume_20d_avg": 1500000,
    "foreign_room_pct": 5.0,
    "status": "Normal"
  }
]
```

Trường `status` tuỳ chọn — nếu xuất hiện và có giá trị Kiểm soát/Hạn chế/Tạm ngừng, screener sẽ skip (giống quy ước cho cash equities).

## 4 yếu tố chấm điểm

Mỗi yếu tố đạt → +1 điểm. Tổng tối đa 4.

| Yếu tố | Ngưỡng "đạt" | Lý do |
| --- | --- | --- |
| **Low Tracking Error** | `tracking_error_pct ≤ 1.0` | TE thấp = ETF bám sát index, ít drift |
| **Low Premium/Discount** | abs(market − NAV) / NAV ≤ 1.0% | Premium/discount thấp = market efficient, ít bị overpay/underpay |
| **Low Expense Ratio** | `expense_ratio_pct ≤ 0.7` | Phí thấp = lợi suất net cao hơn dài hạn |
| **High Liquidity** | `volume_20d_avg ≥ 100,000` | Volume cao = vào/thoát dễ, spread nhỏ |

## Grade

| Score | Grade |
| --- | --- |
| 4 | A — Core-eligible, dùng được làm passive sleeve |
| 3 | B — Cân nhắc, monitor 1-2 yếu tố yếu |
| 2 | C — Có vấn đề, không khuyến nghị Core |
| 1 | D — Tránh |
| 0 | F — Loại |

## Calibration VN-specific

- **Tracking error 1.0%** thấp hơn ngưỡng thị trường phát triển (US ETF benchmarks ~0.1-0.3%) vì:
  - Volume thấp hơn → market maker arbitrage kém efficient
  - Một số rổ VN có constraint room ngoại (`vn-foreign-ownership.md`) → khó replicate đầy đủ
- **Premium/discount 1.0%** chấp nhận được vì market ở VN không có authorised participant mechanism như US
- **Expense ratio 0.7%** cao hơn ETF US (~0.1%) — phản ánh chi phí quản lý ở thị trường nhỏ
- **Volume 100,000 CCQ/phiên** = ngưỡng đủ để mua/bán 1-2 tỷ VND không slippage

## Tham chiếu vn-market-mechanics

- [`vn_foreign_ownership.md`](../../vn-market-mechanics/references/vn_foreign_ownership.md) — `foreign_room_pct` của ETF khác với cổ phiếu thường: VN Diamond ETF được kích chuộc theo NAV nên hiệu chỉnh room ngoại chính xác hơn cổ phiếu blue-chip kín room
- [`vn_fees_and_taxes.md`](../../vn-market-mechanics/references/vn_fees_and_taxes.md) — phí giao dịch ETF == phí cổ phiếu (0.15%/lệnh + 0.1% thuế bán); không có thuế cổ tức nội bộ ETF vì quỹ đã chi phí ở cấp portfolio
- [`vn_price_limits_orders.md`](../../vn-market-mechanics/references/vn_price_limits_orders.md) — ETF tuân thủ biên độ ±7% (HOSE) như cổ phiếu, lô tròn 100, tick 10-100 VND theo band

## Lưu ý khi áp dụng

- Chỉ số NAV/price thường update **end-of-day** — không phù hợp intraday signal
- Khi rebalance index (VN30 mỗi 6 tháng) → tracking error có thể spike ngắn hạn; lấy median TE 3 tháng để smoothing
- ETF mới (<6 tháng niêm yết) có volume thấp → kết quả screener không đáng tin; chờ thêm history
