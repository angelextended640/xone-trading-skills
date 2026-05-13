# VN CANSLIM Screener — Phương pháp luận

Phương pháp CANSLIM của William O'Neil cần được tinh chỉnh cho thị trường Việt Nam vì:

- Không có 13F filings / mutual fund holdings public → I (Institutional Sponsorship) phải dùng proxy
- Biên độ giá ±7% (HOSE) / ±10% (HNX) / ±15% (UPCOM) → định nghĩa "near 52-week high" cần lưới rộng hơn US
- Foreign room (49% mặc định, 30% với ngân hàng) là VN-only concept; foreign net flow là proxy tốt cho dòng tiền tổ chức
- T+2.5 settlement → setup CANSLIM breakout có risk T+ nếu thị trường chung yếu trong 2 phiên đầu sau entry

## 5 trụ cột chấm điểm (mỗi trụ cột +1 điểm, tổng tối đa 5)

### 1. C & A — Current Earnings + Annual Earnings

**Ngưỡng VN:** `eps_growth_yoy_pct >= 20.0`

- Yêu cầu EPS YoY tăng ≥ 20% so với cùng kỳ năm trước
- Nguồn dữ liệu: `vn-data-fetcher fundamentals --period quarter` → `eps_growth_yoy_pct`
- O'Neil gốc: 25% tăng trưởng quý gần nhất, 20%-25% tăng trưởng năm; VN dùng đơn giản 20% YoY vì BCTC quarterly ổn định hơn

### 2. N — New High

**Ngưỡng VN:** `price >= high_52w * 0.95` (cách đỉnh 52w tối đa 5%)

- O'Neil: breakout từ vùng base trong 15% gần đỉnh
- VN: chặt hơn (5%) vì biên độ ±7%/phiên → breakout 1-2 phiên đã chạm đỉnh; xa đỉnh 5% thường nghĩa là đang base
- Nguồn: `vn-data-fetcher ohlcv` rồi tính `high_52w = max(close[-252:])`

### 3. S — Supply & Demand (Volume)

**Ngưỡng VN:** `volume_20d_avg >= 100,000 CP`

- Liquidity bar: dưới 100k/phiên → không đủ vào/ra mà không slippage cho retail >100M VND
- O'Neil gốc còn yêu cầu volume spike trong ngày breakout; phần này để Claude phân tích qua `vn-vcp-screener` hoặc chart trực quan
- Nguồn: `vn-data-fetcher ohlcv` → mean(volume[-20:])

### 4. L — Leader (Relative Strength)

**Ngưỡng VN:** `rs_rating >= 80` (tương đương IBD RS ≥ 80)

- RS rating tính qua return của symbol so với VN-Index lookback 252 phiên, normalize 0-100
- VN có thể dùng output của `vn-sector-analyst` để xác định **ngành dẫn dắt** (đầu tư bổ sung); CANSLIM L = cá nhân mạnh hơn 80% universe + ở trong ngành đang lead
- Mã trong ngành risk-off → giảm 1 grade, kể cả khi RS cao

### 5. I — Institutional Sponsorship (proxy: Foreign Flow)

**Ngưỡng VN:** `foreign_net_buy_10d_vnd >= 0` (mua ròng trong 10 phiên)

- VN không có 13F-equivalent → dùng dòng tiền khối ngoại làm proxy cho "tổ chức"
- Mua ròng > 0 trong 10 phiên gần nhất → có tổ chức tham gia
- Nguồn: `vn-data-fetcher foreign-flow` (point-in-time snapshot) hoặc `vn-foreign-room-tracker history` (10-day change in room_used)
- **Caveat:** Foreign flow chỉ phản ánh nhà đầu tư nước ngoài. Tổ chức trong nước (CTCK / quỹ nội) không có public flow data → proxy này có blind spot

### M — Market Direction (qualitative)

Không tính điểm; chỉ là filter:

- Yêu cầu **`vn-sector-analyst regime != "risk-off"`**
- Nếu thị trường chung downtrend rõ (VN-Index dưới MA50 + MA50 dưới MA200, hoặc FTD chưa confirm), **không** giải ngân kể cả cổ phiếu Grade A
- Cách check: chạy `vn-sector-analyst --ohlcv-glob 'reports/vn_ohlcv_*.json'` → trường `regime` ở output

## Xếp loại

| Score | Grade | Hành động |
| --- | --- | --- |
| 5/5 | A | Ứng viên xuất sắc, đưa vào watchlist + đăng ký thesis qua `vn-trader-memory` |
| 4/5 | B | Tiềm năng, monitor 1 trụ cột yếu |
| 3/5 | C | Quan sát, không trade |
| ≤ 2/5 | C | Bỏ qua |

## Status flag filter (mặc định)

Mặc định skill skip cổ phiếu có `status` ∈ {`Kiểm soát`, `Hạn chế`, `Tạm ngừng`, `Cảnh báo`} — các flag này thường đi kèm cắt margin + giảm thanh khoản → setup CANSLIM mất ý nghĩa.

Pass `--include-flagged` để bypass filter (use case: nghiên cứu, không giao dịch thực).

## Tham chiếu vn-market-mechanics

- [`vn_trading_rules.md`](../../vn-market-mechanics/references/vn_trading_rules.md) — status flags, T+2.5, sessions
- [`vn_price_limits_orders.md`](../../vn-market-mechanics/references/vn_price_limits_orders.md) — biên độ giá ảnh hưởng N pillar (52w high definition)
- [`vn_foreign_ownership.md`](../../vn-market-mechanics/references/vn_foreign_ownership.md) — foreign flow proxy cho I pillar
- [`vn_data_sources.md`](../../vn-market-mechanics/references/vn_data_sources.md) — vnstock fundamentals + foreign-flow endpoints

## Cấu trúc Universe JSON

```json
[
  {
    "symbol": "FPT",
    "price": 135000,
    "high_52w": 136000,
    "volume_20d_avg": 2500000,
    "eps_growth_yoy_pct": 22.5,
    "rs_rating": 85,
    "foreign_net_buy_10d_vnd": 50000000000,
    "sector": "Công nghệ thông tin",
    "status": "Normal"
  }
]
```

| Trường | Bắt buộc | Mô tả |
| --- | --- | --- |
| `symbol` | có | Mã CP |
| `price` | có | Giá hiện tại (VND) |
| `high_52w` | có | Đỉnh 52 tuần (VND) |
| `volume_20d_avg` | có | Volume bình quân 20 phiên |
| `eps_growth_yoy_pct` | có | % tăng EPS YoY |
| `rs_rating` | có | 0-100 |
| `foreign_net_buy_10d_vnd` | có | Mua ròng NN 10 phiên (VND) — âm = bán ròng |
| `sector` | tuỳ chọn | Hiển thị trong báo cáo |
| `status` | tuỳ chọn | Nếu = Kiểm soát/Hạn chế/Tạm ngừng → skip |
