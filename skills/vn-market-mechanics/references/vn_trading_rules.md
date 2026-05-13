# Quy tắc giao dịch — Thị trường chứng khoán Việt Nam

**Last updated:** 2026-05-12
**Nguồn chính:** HOSE, HNX, UBCKNN

## 1. Ba sàn giao dịch

| Sàn | Tên đầy đủ | Đặc điểm | Số mã (xấp xỉ) |
| --- | --- | --- | --- |
| HOSE | Sở GDCK TP.HCM | Cổ phiếu niêm yết chính, blue-chip (VN30) | ~400 |
| HNX | Sở GDCK Hà Nội | Cổ phiếu niêm yết thứ cấp, HNX30 | ~330 |
| UPCOM | Sàn giao dịch CK chưa niêm yết | Công ty đại chúng chưa lên HOSE/HNX | ~860 |

Chỉ số chính: **VN-Index** (HOSE), **VN30** (30 cổ phiếu vốn hoá lớn nhất HOSE), **HNX-Index**, **UPCOM-Index**.

## 2. Giờ giao dịch (giờ Việt Nam, UTC+7)

### Phiên cơ sở (cổ phiếu, chứng chỉ quỹ)

| Phiên | HOSE | HNX | UPCOM |
| --- | --- | --- | --- |
| Mở cửa định kỳ (ATO) | 09:00 – 09:15 | — | — |
| Khớp liên tục sáng | 09:15 – 11:30 | 09:00 – 11:30 | 09:00 – 11:30 |
| Nghỉ trưa | 11:30 – 13:00 | 11:30 – 13:00 | 11:30 – 13:00 |
| Khớp liên tục chiều | 13:00 – 14:30 | 13:00 – 14:30 | 13:00 – 15:00 |
| Đóng cửa định kỳ (ATC) | 14:30 – 14:45 | 14:30 – 14:45 | — |
| Khớp thoả thuận | 09:00 – 11:30, 13:00 – 15:00 | 09:00 – 11:30, 13:00 – 15:00 | 09:00 – 11:30, 13:00 – 15:00 |

Giao dịch **không** diễn ra vào thứ Bảy, Chủ Nhật và ngày lễ Việt Nam (Tết Âm lịch, 30/4, 1/5, 2/9, v.v.).

### Phiên phái sinh (VN30 Futures)

| Phiên | Giờ |
| --- | --- |
| Trước giờ | 08:45 – 09:00 |
| Khớp liên tục sáng | 09:00 – 11:30 |
| Nghỉ trưa | 11:30 – 13:00 |
| Khớp liên tục chiều | 13:00 – 14:30 |
| Khớp định kỳ đóng cửa | 14:30 – 14:45 |

## 3. Chu kỳ thanh toán T+2.5

**Quy ước:** Cổ phiếu/CCQ tại HOSE/HNX/UPCOM thanh toán **T+2** (theo ngày làm việc) nhưng nhà đầu tư chỉ có thể **bán** vào chiều ngày T+2 sau khi cổ phiếu về tài khoản (~12:30 PM). Do đó thị trường thường gọi là **T+2.5**.

| Ngày | Ý nghĩa | Có thể làm gì |
| --- | --- | --- |
| T+0 | Ngày khớp lệnh mua | Tiền tạm giữ; cổ phiếu chưa về tài khoản |
| T+1 | 1 ngày làm việc sau | Cổ phiếu vẫn chưa thể bán |
| T+2 (sáng) | 2 ngày làm việc sau | Cổ phiếu chưa về |
| T+2 (~12:30 PM) | Cổ phiếu được ghi nhận | **Có thể bán từ phiên chiều T+2** |

**Hệ quả thực tiễn cho swing trader:**

- Không thể "lướt sóng trong ngày" (intraday) như cổ phiếu Mỹ
- Stop-loss giả định bằng **giá đóng cửa**, không phải intraday, vì cổ phiếu mới mua không bán được intraday cho đến T+2.5
- Vốn tái sử dụng có độ trễ — quản lý tiền mặt cần tính đến T+2.5

**Phái sinh (VN30 Futures):** Thanh toán **T+0** — có thể đóng vị thế trong ngày, không bị T+2.5.

## 4. Bán khống (Short Selling)

- **Cổ phiếu cơ sở:** Bán khống **chưa được phép** ở Việt Nam (ngoại trừ một số nghiệp vụ chuyên biệt như hoán đổi cổ phiếu, lend/borrow chính thức theo cơ chế đặc biệt). Nhà đầu tư cá nhân **không thể** short cổ phiếu HOSE/HNX/UPCOM.
- **Phái sinh:** Có thể **short VN30 Futures** (bán hợp đồng tương lai). Đây là cách hợp pháp duy nhất để có exposure âm với chỉ số VN30.

Hệ quả: Mọi chiến lược "parabolic short" hay "weak-stock short" của Mỹ **không áp dụng trực tiếp** cho cổ phiếu cơ sở VN. Nếu cần hedge, dùng VN30 Futures.

## 5. Ký quỹ (Margin)

- Công ty CK cấp **margin** cho nhà đầu tư theo tỷ lệ quy định bởi UBCKNN
- Mỗi cổ phiếu có **tỷ lệ ký quỹ** riêng (thường 50%, có mã 30%/40%, một số mã không được margin)
- Danh sách mã margin và tỷ lệ do từng CTCK công bố (cập nhật định kỳ)
- Mã bị **call margin** (force-sell) khi tỷ lệ tài sản ròng/dư nợ giảm dưới ngưỡng (thường 30-35%)
- Mã **không được margin** thường là: cảnh báo, kiểm soát, hạn chế giao dịch, hoặc bị đưa vào diện đặc biệt

## 6. Tình trạng cảnh báo

UBCKNN/Sở GDCK gắn nhãn các mã có vấn đề:

| Nhãn | Ý nghĩa | Hệ quả |
| --- | --- | --- |
| Bình thường | Mã đủ điều kiện giao dịch | Không hạn chế |
| Cảnh báo | Vi phạm điều kiện công bố thông tin / lợi nhuận âm | Vẫn giao dịch bình thường nhưng cần thận trọng |
| Kiểm soát | Vi phạm nặng hơn | Giao dịch hạn chế (chỉ phiên ATC tại HOSE) |
| Hạn chế giao dịch | Vi phạm rất nghiêm trọng | Chỉ giao dịch trong phiên duy nhất (chiều) |
| Tạm ngừng | Vi phạm cực nặng / đang tái cơ cấu | Không giao dịch được |

**Quy tắc đề xuất:** Skill sàng lọc/lập kế hoạch giao dịch **mặc định loại trừ** cổ phiếu trong diện Kiểm soát/Hạn chế/Tạm ngừng trừ khi người dùng yêu cầu rõ ràng.
