# Phí giao dịch và thuế — TTCK Việt Nam

**Last updated:** 2026-05-12
**Nguồn:** UBCKNN, các CTCK chính (SSI, VPS, VNDirect, HSC, MBS, TCBS, DNSE)

## 1. Phí môi giới (broker commission)

Phí môi giới do từng CTCK tự đặt, **không** thống nhất. Khoảng phổ biến (T05/2026):

| CTCK | Cổ phiếu cơ sở (mua/bán) | Phái sinh (HĐ tương lai) |
| --- | --- | --- |
| **VPS** | 0.15% (online) – 0.30% (truyền thống) | 2,700 VND/HĐ |
| **SSI** | 0.15% – 0.25% | 3,000 VND/HĐ |
| **VNDirect** | 0.15% – 0.35% | 3,000 VND/HĐ |
| **HSC** | 0.15% – 0.35% | 2,700 VND/HĐ |
| **MBS** | 0.12% – 0.30% | 2,700 VND/HĐ |
| **TCBS** | 0.10% – 0.15% | 2,500 VND/HĐ |
| **DNSE** | **0.03% – 0.05%** (rất thấp) | 1,000 – 2,500 VND/HĐ |

**Quy tắc skill mặc định:** Dùng **0.15%/lệnh** cho cổ phiếu cơ sở (mỗi chiều mua và bán), trừ khi người dùng cấp giá trị khác. Đây là mức phổ biến cho tài khoản online cơ bản.

**Phí tối thiểu:** Một số CTCK áp dụng phí tối thiểu (ví dụ 50,000 VND/lệnh). Bỏ qua nếu lệnh không lớn.

## 2. Thuế khi bán (capital gains tax)

- **0.1% trên giá trị bán** (chỉ áp dụng khi bán; không áp dụng khi mua)
- Thu thuế **tại nguồn** bởi CTCK; nhà đầu tư không cần tự kê khai cho mỗi giao dịch
- Áp dụng cho **mọi nhà đầu tư cá nhân** (kể cả lỗ vẫn phải nộp 0.1% trên giá trị bán — không có khái niệm capital loss offset)
- Áp dụng cho cổ phiếu, chứng chỉ quỹ, trái phiếu doanh nghiệp

**Ví dụ:** Bán 1,000 VIC giá 46,000 VND → giá trị 46,000,000 → thuế 46,000 VND

## 3. Thuế cổ tức (dividend tax)

- **Cổ tức tiền mặt:** 5% trên số tiền cổ tức nhận (giữ tại nguồn bởi công ty trả cổ tức)
- **Cổ tức bằng cổ phiếu:** 5% trên giá trị tính theo mệnh giá (10,000 VND/CP) tại thời điểm chia, thu khi nhà đầu tư **bán** cổ phiếu nhận từ cổ tức

**Ví dụ:** Nhận 5,000 VND/CP cổ tức trên 1,000 VIC → cổ tức gộp 5,000,000 → thuế 250,000 → nhận thực tế 4,750,000

## 4. Phí khác

| Khoản phí | Mức | Ghi chú |
| --- | --- | --- |
| Phí lưu ký (VSDC) | 0.27 VND/CP/tháng | Tự động trừ từ tài khoản hàng tháng |
| Phí UBCKNN | 0.02% trên giá trị giao dịch | Do CTCK thu hộ |
| Phí chuyển nhượng | Tùy CTCK | Khi chuyển CP giữa các tài khoản khác chủ |
| Phí ứng trước tiền bán | ~0.04%/ngày | Khi muốn dùng tiền bán T+1/T+2 trước khi thanh toán |
| Phí margin (lãi vay margin) | 12-14%/năm | Tùy CTCK và quy mô vay |

## 5. Phí phái sinh

| Khoản phí | Mức (T05/2026) |
| --- | --- |
| Phí môi giới CTCK | 1,000 – 3,000 VND/HĐ (mỗi chiều) |
| Phí giao dịch HNX | 2,700 VND/HĐ |
| Phí thanh toán VSDC | 2,550 VND/HĐ |
| Phí quản lý vị thế qua đêm | ~3,000 VND/HĐ |
| Thuế bán | **Không** áp dụng cho phái sinh (khác với cổ phiếu cơ sở) |

**Tổng phí phổ biến mỗi HĐ phái sinh (round-trip):** ~15,000 – 20,000 VND

## 6. Công thức tính lợi nhuận sau phí và thuế

### Mua-bán cổ phiếu cơ sở (long)

```
Phí mua    = Giá trị mua × phí_môi_giới%
Phí bán    = Giá trị bán × phí_môi_giới%
Thuế bán   = Giá trị bán × 0.001  (0.1%)
Lãi gộp    = Giá trị bán − Giá trị mua
Lãi ròng   = Lãi gộp − Phí mua − Phí bán − Thuế bán
```

**Ví dụ:** Mua 1,000 VIC @ 45,000, bán @ 48,000 (phí 0.15%, thuế 0.1%):

- Giá trị mua: 45,000,000 / Phí mua: 67,500
- Giá trị bán: 48,000,000 / Phí bán: 72,000 / Thuế bán: 48,000
- Lãi gộp: 3,000,000
- **Lãi ròng: 3,000,000 − 67,500 − 72,000 − 48,000 = 2,812,500 VND**
- Hệ số giảm so với lãi gộp: ~6.25% (phí + thuế "ăn" 6.25% lợi nhuận)

### Break-even điểm

Để hoà vốn sau phí và thuế, giá bán phải vượt giá mua ít nhất:

```
% break-even = phí_mua% + phí_bán% + thuế_bán%
            ≈ 0.15% + 0.15% + 0.1%
            = 0.40% (làm tròn)
```

Một số CTCK rẻ (DNSE): 0.03% + 0.03% + 0.1% = **0.16%**.

## 7. Hệ quả cho skill `vn-position-sizer`

1. Khi tính số tiền rủi ro (`risk_per_share`), **nên trừ phí và thuế ước tính** từ giá thoát lý thuyết để có rủi ro thực
2. Mặc định `--broker-fee-pct 0.15` và `--sale-tax-pct 0.1`
3. Báo cáo phải hiển thị: phí mua, phí bán, thuế bán, lãi ròng dự kiến

## 8. Hệ quả cho skill `vn-portfolio-manager` / `vn-tax-fee-calculator`

1. Tính lợi nhuận portfolio **sau phí và thuế** mới phản ánh thực tế
2. Cổ tức tiền mặt: trừ 5% trước khi cộng vào tổng lợi nhuận
3. So sánh chiến lược ngắn hạn vs dài hạn cần kể đến phí (chiến lược lướt sóng cao tần bị "ăn" nhiều phí hơn)
