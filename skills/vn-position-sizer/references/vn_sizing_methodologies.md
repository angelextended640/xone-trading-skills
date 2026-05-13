# Phương pháp tính position size cho cổ phiếu Việt Nam

**Last updated:** 2026-05-13

Tài liệu này trình bày ba phương pháp tính số cổ phiếu tối ưu cho lệnh **mua (long)** trên TTCK Việt Nam, kèm các điều chỉnh đặc thù VN.

## 1. Fixed Fractional (Phương pháp mặc định)

### Công thức

```
rủi_ro_VND      = quy_mô_tài_khoản × %_rủi_ro / 100
rủi_ro_mỗi_CP   = giá_entry − giá_stop
shares_thô      = rủi_ro_VND / rủi_ro_mỗi_CP
shares_cuối     = floor(shares_thô / 100) × 100   ← làm tròn lô 100
```

### Ví dụ

Tài khoản 1 tỷ VND, mua VIC giá 45,000 stop 42,000, rủi ro 1%:

- Rủi ro VND: 1,000,000,000 × 1% = 10,000,000 VND
- Rủi ro mỗi CP: 45,000 − 42,000 = 3,000 VND
- Shares thô: 10,000,000 / 3,000 = 3,333
- **Shares cuối: 3,300 CP** (làm tròn xuống lô 100)
- Vị thế: 3,300 × 45,000 = 148,500,000 VND
- Rủi ro thực: 3,300 × 3,000 = 9,900,000 VND (0.99% — hơi thấp hơn target do làm tròn)

### Khi nào dùng

- Là **mặc định** cho mọi giao dịch swing
- Khi bạn có niềm tin về setup nhưng không có dữ liệu thống kê cụ thể
- Đơn giản, đủ tốt cho 90% trường hợp

### Hướng dẫn % rủi ro

| %rủi ro | Đối tượng | Cảnh báo |
| --- | --- | --- |
| 0.5% | Newbie, account < 200tr VND | Rất an toàn nhưng kết quả phẳng |
| **1.0%** | **Mặc định cho swing trader có kỷ luật** | **Tối ưu cho hầu hết** |
| 1.5% | Trader có hệ thống chứng minh win-rate > 50% | Cần kỷ luật cao |
| 2.0% | Hiếm, chỉ khi setup A+ tuyệt đối | Một chuỗi 5 lệnh thua = −10% account |
| >2% | Không khuyến nghị | Một chuỗi 10 lệnh thua = −20%+ |

## 2. ATR-Based (Volatility-Adjusted)

### Khái niệm

ATR (Average True Range) đo độ biến động trung bình của cổ phiếu trong N phiên (thường 14). Cổ phiếu biến động mạnh cần stop xa hơn → ít CP hơn.

### Công thức

```
stop_distance   = ATR × ATR_multiplier   (thường ×2.0)
stop_price      = giá_entry − stop_distance, làm tròn theo bước giá VN
rủi_ro_mỗi_CP   = stop_distance
shares          = floor((rủi_ro_VND / stop_distance) / 100) × 100
```

### Ví dụ

Tài khoản 500tr VND, mua HPG giá 28,000, ATR=800, multiplier=2.0, rủi ro 1%:

- Stop distance: 800 × 2.0 = 1,600 VND
- Stop price thô: 28,000 − 1,600 = 26,400 → làm tròn xuống tick 50 → **26,400**
- Rủi ro VND: 5,000,000
- Shares thô: 5,000,000 / 1,600 = 3,125
- **Shares cuối: 3,100 CP**
- Vị thế: 86,800,000 VND
- ⚠️ Kiểm tra giá sàn HPG: floor = 28,000 × 0.93 = 26,040 → 26,050 (làm tròn lên tick 50). Stop 26,400 > floor 26,050 → **OK**

### Khi nào dùng

- Cổ phiếu volatile (biotech VN, cổ phiếu speculative)
- Khi bạn muốn stop "thoáng" với mã có swing rộng
- Khi setup là breakout từ vùng tích luỹ (stop thường ATR×1.5)

### Hướng dẫn ATR multiplier

| Multiplier | Loại setup | Lý do |
| --- | --- | --- |
| 1.0× | Mean reversion, đặt cược nhanh | Stop chặt, win rate cao bù lỗ nhỏ |
| **2.0×** | **Trend follow / breakout** | **Mặc định** |
| 2.5× | Position trade dài hạn | Cho phép pullback sâu |
| 3.0×+ | Long-term hold | Stop xa, ít bị shake-out |

### Cảnh báo VN-specific

Vì biên độ tối đa hàng phiên là 7-15%, nếu `ATR × multiplier > biên_độ × entry_price`, stop của bạn sẽ **không thể** hiệu lực trong phiên giảm sàn (vì giá ngừng tại sàn). Skill sẽ cảnh báo nếu `stop_price < floor_price`.

## 3. Kelly Criterion

### Công thức

```
W = win_rate (xác suất thắng, 0-1)
R = avg_win / avg_loss (tỷ lệ win/loss bình quân)

Kelly% = W − (1 − W) / R
Half-Kelly% = Kelly% / 2   ← khuyến nghị thực tế
```

### Ví dụ

Win rate 55%, avg win 2.5R, avg loss 1.0R:

- R = 2.5 / 1.0 = 2.5
- Kelly = 0.55 − (1 − 0.55) / 2.5 = 0.55 − 0.18 = **0.37 (37%)**
- Half Kelly = **18.5%**

Với tài khoản 1 tỷ VND, half-Kelly đề nghị **risk budget = 185 triệu VND** cho **toàn bộ portfolio**, không phải mỗi lệnh.

### Khi nào dùng

- Khi bạn có **ít nhất 30-50 lệnh** thống kê win-rate và R-multiple đáng tin
- Để xác định **risk budget tổng** cho portfolio, không phải mỗi lệnh
- Trader có hệ thống ổn định và journal đầy đủ

### Cảnh báo

- **Không bao giờ dùng full Kelly** thực tế — biến động vốn rất mạnh
- **Half-Kelly** vẫn nắm ~75% growth với độ biến động thấp hơn nhiều
- Nếu Kelly% âm (W − (1−W)/R < 0) → **hệ thống có expected value âm, không nên trade**
- Win-rate cao có thể do **survivorship bias** — kiểm tra lại data

## 4. So sánh

| Phương pháp | Ưu | Nhược | Phù hợp |
| --- | --- | --- | --- |
| Fixed Fractional | Đơn giản, ổn định, dễ kỷ luật | Không tính volatility | Mặc định mọi trader |
| ATR-Based | Tự điều chỉnh theo volatility | Cần dữ liệu ATR; phức tạp hơn | Mã volatile, breakout |
| Kelly | Toán học tối ưu | Cần data thống kê chính xác | Trader có hệ thống ổn định |

**Khuyến nghị:** Dùng Fixed Fractional 1% làm mặc định. Chuyển sang ATR khi cổ phiếu rõ ràng volatile. Dùng Kelly để xác định **tổng risk budget** portfolio, sau đó phân bổ về Fixed Fractional cho từng lệnh.

## 5. Ràng buộc portfolio (áp lên mọi phương pháp)

### Max position per stock (mặc định 10%)

```
max_shares_by_pos = (account × max_pos% / 100 / entry_price)
                    → round down to lot of 100
```

### Max sector exposure (mặc định 30%)

```
remaining_sector = max_sector% − current_sector%
max_shares_by_sector = (account × remaining_sector / 100 / entry_price)
                       → round down to lot of 100
```

### Tổng portfolio heat (khuyến nghị 6-8%)

Tổng rủi ro mở (sum of all `final_risk_vnd` trên mọi vị thế đang mở) không nên vượt 6-8% account.

### Thứ tự áp dụng

```
shares = min(
  risk_based_shares,
  max_position_shares,
  max_sector_shares,
  available_cash_shares
)
```

**Ràng buộc nào chặt nhất → quyết định size cuối.** Skill sẽ đánh dấu `binding_constraint`.

## 6. Quy tắc VN-specific bổ sung

### Làm tròn lô 100

```python
shares_cuối = (shares_thô // 100) * 100
```

Luôn `floor`, không bao giờ `round` hay `ceil`. Lý do: làm tròn lên có thể vượt risk budget; rủi ro tăng > target.

### Stop dưới giá sàn = nguy hiểm

Nếu `stop_price < floor_price` của phiên đầu sau khi mua, biên độ sẽ chặn lệnh cắt lỗ → bạn có thể chịu lỗ 7-15% trong phiên đầu trước khi exit được. **Skill phải cảnh báo.**

Có 2 lựa chọn khi gặp tình huống này:
1. **Lùi stop lên trên giá sàn** (chấp nhận stop xa hơn, ít CP hơn)
2. **Giảm size** sao cho rủi ro tối đa (đến floor) vẫn nằm trong budget

### Tính phí và thuế vào break-even

Lợi nhuận thực = lãi gộp − phí mua − phí bán − thuế bán (0.1%)
Break-even ≈ giá entry × (1 + 0.4%) khi phí 0.15%/lệnh.
Một lệnh "đi ngang" nhỏ thực ra **âm** sau phí và thuế.

### T+2.5 và quản trị vốn

- Tiền dùng mua hôm nay **chỉ về** sau khi bán → T+2 (~chiều)
- Nếu định trade rotational nhanh, dự phòng cash flow tránh thiếu vốn
- "Ứng trước tiền bán" mất ~0.04%/ngày — đắt cho holding ngắn

## 7. Checklist trước khi đặt lệnh

- [ ] Đã xác định setup rõ ràng (breakout / pullback / VCP / earnings)?
- [ ] Đã tính số CP theo Fixed Fractional 1%?
- [ ] Stop có nằm trên giá sàn của phiên đầu?
- [ ] Đã làm tròn xuống lô 100?
- [ ] Vị thế ≤ 10% account?
- [ ] Tổng exposure ngành ≤ 30%?
- [ ] Total portfolio heat (open risk) ≤ 6-8%?
- [ ] Có ghi lại thesis vào journal?
- [ ] Biết phải kiểm tra gì để invalidate setup?
