# VN Event Impact Window

**Last updated:** 2026-05-13

Mỗi loại sự kiện có một **cửa sổ tác động** đặc trưng — khoảng thời gian thị trường tiêu hoá thông tin. Tham khảo này giúp xác định:

1. Khi nào nên **reduce position size** trước sự kiện
2. Khi nào nên **tránh new entries**
3. Khi nào sự kiện đã "priced in" và an toàn để giao dịch

## Bảng cửa sổ tác động

| Sự kiện | Pre-event window | Event day | Post-event window | Tổng thời gian impact |
| --- | --- | --- | --- | --- |
| **SBV — thay đổi lãi suất điều hành** | 1-3 phiên trước (rumour) | High volatility | 5-10 phiên | 2-3 tuần |
| **SBV — OMO routine** | 0 | Minor | 1 phiên | Cuối phiên đó |
| **SBV — can thiệp tỷ giá** | 0-1 phiên | High volatility | 3-5 phiên | 1-2 tuần |
| **GSO CPI release** | 1-2 phiên (expectation building) | Medium volatility | 2-3 phiên | 1 tuần |
| **GSO GDP release** | 2-3 phiên (anticipation) | High volatility | 3-5 phiên | 1-2 tuần |
| **GSO FDI release** | 0 | Low-medium | 1-2 phiên | 2-3 phiên |
| **GSO bán lẻ / IIP** | 0 | Low | 1 phiên | 1 phiên |
| **FOMC quyết định** | 1-3 phiên (vốn ngoại defensive) | Pre-market gap | 3-7 phiên | 1-2 tuần |
| **Non-Farm Payrolls** | 0 | Friday US, react Monday VN | 1-3 phiên VN | 1 tuần |
| **CPI Mỹ** | 0 | Mid-month, react ngay | 2-5 phiên | 1-2 tuần |
| **Q4 KQKD season (toàn thị trường)** | Tháng 1-2 cả mùa | Per-symbol | Per-symbol | Cả tháng |
| **AGM (Annual General Meeting) blue-chip** | 1 tuần | Per-event | 2-5 phiên | 1-2 tuần |
| **Ex-rights date (cổ tức / phát hành)** | 0 | Auto giá điều chỉnh | 0 | 1 phiên (cơ học) |
| **Nghỉ Tết** | 1-2 tuần trước (chốt lãi) | 5-7 ngày nghỉ | 1 tuần (thanh khoản thấp) | 3-4 tuần |
| **Quarter-end (31/3, 30/6, 30/9, 31/12)** | 1-2 phiên (window dressing) | 0 | 1-2 phiên | 1 tuần |

## Diễn giải

### "High volatility" cảnh báo

Trong những phiên này:
- **VN-Index có thể di động ±1-2%** trong một phiên (vs trung bình ±0.5%)
- **Volume tăng đột biến** 1.5-3x bình thường
- **Spread bid-ask rộng hơn** đối với mã thanh khoản kém
- **Lệnh stop có thể slip** xa pivot do gap mở cửa

### Action playbook theo từng cửa sổ

#### Pre-event (1-3 phiên trước sự kiện lớn)

- **Reduce new entries**: chỉ vào những setup A+ với conviction cao
- **Tighten stops** trên positions đang có lãi
- **Increase cash** nếu sự kiện có thể di chuyển market ±2%
- **Document expectation**: ghi trong journal kỳ vọng của bạn trước sự kiện

#### Event day

- **No new entries** trong 30 phút đầu phiên (chờ gap stabilize)
- **Follow-the-trend**: nếu market đi theo expectation, giữ position; nếu ngược, exit
- **Manual exit trigger**: nếu position bị gap dưới stop, exit at open, không chờ rally

#### Post-event (3-10 phiên sau)

- **Re-evaluate trade plan** dựa trên reaction
- **Wait for trend confirmation**: ít nhất 2-3 phiên ổn định trước khi vào new positions
- **Sector tilt may have shifted**: trigger `vn-sector-analyst` lại

## Sự kiện "Priced In" và sự kiện "Surprise"

### Priced in events

Phản ứng nhỏ — market đã expect:
- FOMC quyết định theo dot plot (no surprise)
- CPI VN theo trend hiện tại
- GDP tăng trưởng ổn định (gần consensus)

→ **Volatility bình thường**, có thể trade gần sự kiện.

### Surprise events

Phản ứng lớn — market không expect:
- FOMC hawkish hơn dot plot (surprise rate hike)
- CPI vượt trên/dưới consensus > 0.5%
- SBV thay đổi lãi suất giữa kỳ
- GDP miss > 0.5%
- Quân sự / địa chính trị bất ngờ

→ **Volatility cao, gap risk lớn**, nên defensive sizing.

## Combine với position-sizer

Trong tuần có sự kiện lớn:

```bash
# Giảm risk_pct từ 1.0% xuống 0.5% — cho phép thêm cushion
python skills/vn-position-sizer/scripts/vn_position_sizer.py \
  --account-size 1000000000 \
  --symbol FPT \
  --entry 142000 --stop 135000 \
  --risk-pct 0.5 \
  --output-dir reports/
```

Hoặc tăng ATR multiplier để giãn stop xa hơn (cushion gap):

```bash
python skills/vn-position-sizer/scripts/vn_position_sizer.py \
  --account-size 1000000000 \
  --symbol FPT --entry 142000 \
  --atr 3000 --atr-multiplier 3.0 \
  --risk-pct 1.0 \
  --output-dir reports/
```

## Quy tắc nhanh

1. **3 phiên trước FOMC**: hạn chế new entries
2. **Ngày công bố CPI VN (~30 hàng tháng)**: theo dõi closely, có thể trade reaction sau công bố
3. **Tuần trước Tết**: defensive — nhiều người chốt lãi, thanh khoản giảm
4. **Sau Tết 1 tuần**: thanh khoản còn thấp, đợi orderly trading trở lại
5. **Quarter-end window dressing**: blue-chip thường được "tô son" — không trade contrarian
