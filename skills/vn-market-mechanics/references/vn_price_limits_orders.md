# Biên độ giá, lô giao dịch, và loại lệnh — TTCK Việt Nam

**Last updated:** 2026-05-12
**Nguồn:** HOSE, HNX, UPCOM

## 1. Biên độ giá hàng ngày

Mỗi sàn có **biên độ dao động giá tối đa** trong một phiên giao dịch, tính từ **giá tham chiếu** (thông thường là giá đóng cửa phiên trước).

| Sàn | Cổ phiếu thường | Ngày đầu niêm yết / sau tạm ngừng | Chứng quyền (CW) | ETF / CCQ |
| --- | --- | --- | --- | --- |
| **HOSE** | ±7% | ±20% | Tính riêng từ CW công thức | ±7% |
| **HNX** | ±10% | ±30% | n/a | ±10% |
| **UPCOM** | ±15% | ±40% | n/a | ±15% |

**Giá trần** = giá tham chiếu × (1 + biên độ), làm tròn theo bước giá.
**Giá sàn** = giá tham chiếu × (1 − biên độ), làm tròn theo bước giá.

**Ví dụ HOSE:** Mã VIC giá tham chiếu 45,500 VND
- Giá trần: 45,500 × 1.07 = 48,685 → làm tròn theo bước giá → **48,650**
- Giá sàn: 45,500 × 0.93 = 42,315 → **42,300**

**Hệ quả thực tiễn:**

- Một lệnh mua không thể đặt giá > trần; lệnh bán không thể đặt giá < sàn
- Khi cổ phiếu chạm trần (tăng trần) với cầu vượt cung, thường **không khớp đủ** — phải chờ phiên sau
- Một cổ phiếu mua đỉnh có thể bị giảm tối đa 7%/10%/15% **mỗi phiên**, nên **stop-loss thực tế** trong phiên đầu là biên độ sàn nếu rớt giá liên tục

## 2. Lô giao dịch

- **HOSE và HNX:** Lô tròn (round lot) = **100 cổ phiếu**. Lô lẻ (1–99 CP) phải giao dịch qua phiên **lô lẻ** riêng (thường rẻ hơn 1-2 bước giá).
- **UPCOM:** Lô tròn = **100 cổ phiếu** từ 2018 trở đi.
- **Phái sinh VN30 Futures:** Lô = **1 hợp đồng** (multiplier 100,000 VND/điểm; ký quỹ ban đầu khoảng 17-20%).

**Quy tắc tính shares:** Số cổ phiếu mua = **floor(số ước lượng / 100) × 100**.

## 3. Bước giá (tick size)

### HOSE — cổ phiếu

| Khoảng giá | Bước giá |
| --- | --- |
| < 10,000 VND | 10 VND |
| 10,000 – 49,950 VND | 50 VND |
| ≥ 50,000 VND | 100 VND |

### HNX — cổ phiếu

| Tất cả khoảng giá | 100 VND |

### UPCOM — cổ phiếu

| Tất cả khoảng giá | 100 VND |

### Phái sinh VN30 Futures

| Bước giá | 0.1 điểm (= 10,000 VND/HĐ với multiplier 100,000) |

**Quy tắc làm tròn:** Mọi giá trần/sàn/đặt lệnh **phải** làm tròn theo bước giá phù hợp với sàn và khoảng giá.

## 4. Loại lệnh

### Cổ phiếu (HOSE/HNX/UPCOM)

| Mã lệnh | Tên | Mô tả | Sàn áp dụng |
| --- | --- | --- | --- |
| LO | Limit Order | Lệnh giới hạn — đặt giá cụ thể | HOSE, HNX, UPCOM |
| ATO | At The Open | Khớp lệnh tại giá mở cửa định kỳ | HOSE only (09:00–09:15) |
| ATC | At The Close | Khớp lệnh tại giá đóng cửa định kỳ | HOSE, HNX (14:30–14:45) |
| MP | Market Price | Lệnh thị trường — khớp giá đối ứng tốt nhất | HOSE (khớp liên tục) |
| MTL / MOK / MAK | Market-related on HNX | Các biến thể lệnh thị trường HNX | HNX |
| PLO | Post Limit Order | Lệnh khớp sau giờ tại giá đóng cửa | HNX (14:45–15:00) |

### Phái sinh

LO và MTL là phổ biến nhất; MOK (Market-Or-Kill), MAK (Market-And-Kill) cho thực thi nhanh.

## 5. Quy tắc đặc biệt

### Quy định mua-bán cùng phiên (cổ phiếu cơ sở)

- **Không được phép** mua và bán cùng một mã trong cùng phiên (cùng ngày) khi vẫn còn vị thế mua chưa thanh toán T+2.5
- Nói cách khác: cổ phiếu vừa mua hôm nay **không** thể bán ngay hôm nay, ngày mai, hoặc sáng T+2 — phải chờ chiều T+2

### Phiên lô lẻ (odd lot)

- Cổ phiếu lẻ (1–99) chỉ giao dịch ở phiên riêng, thường thấp hơn giá thị trường 1-3 bước giá
- Phát sinh khi có chia tách cổ phiếu, cổ tức bằng cổ phiếu, hoặc mua lô không tròn từ IPO

### Khớp thoả thuận (Put-through)

- Cho phép giao dịch khối lượng lớn (≥20,000 CP HOSE / ≥5,000 CP HNX) với giá thoả thuận trong biên độ
- Không qua orderbook công khai
- Thường dùng giữa các tổ chức / cổ đông lớn

## 6. Hệ quả cho skill `vn-position-sizer`

1. **Lô tròn 100:** Số cổ phiếu cuối cùng = `floor(shares / 100) × 100`
2. **Stop-loss giá:** Phải làm tròn theo bước giá (10/50/100 VND theo sàn và khoảng giá)
3. **Giá trần/sàn:** Stop-loss đề xuất không nên đặt thấp hơn giá sàn cùng phiên (nếu thấp hơn, biên độ sẽ chặn lệnh bán cắt lỗ)
4. **Không hỗ trợ short cổ phiếu cơ sở:** Skill chỉ tính position size cho lệnh **mua (long)**

## 7. Hệ quả cho skill sàng lọc / lập kế hoạch giao dịch VN

1. Cổ phiếu **tăng trần** (giá hiện tại = giá trần) cần đánh dấu — không thể mua thêm trong phiên
2. Cổ phiếu **giảm sàn** cần đánh dấu — không thể bán cắt lỗ trong phiên
3. Lệnh "stop-loss tự động" theo giá intraday **không tồn tại** ở VN broker truyền thống — phải mô phỏng bằng cảnh báo và đặt lệnh thủ công
