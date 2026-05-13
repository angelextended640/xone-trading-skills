---
layout: default
title: Bắt đầu Nhanh (Getting Started)
parent: Tiếng Việt
nav_order: 1
permalink: /vi/getting-started/
---

# Hướng dẫn Bắt đầu Nhanh
{: .no_toc }

Hướng dẫn cài đặt, thiết lập môi trường và chạy thử nghiệm kỹ năng chứng khoán Việt Nam đầu tiên của bạn theo từng bước (Step-by-Step).
{: .fs-6 .fw-300 }

<details open markdown="block">
  <summary>Mục lục</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Điều kiện tiên quyết (Prerequisites)

Để sử dụng bộ kỹ năng `vn-*`, bạn cần chuẩn bị các công cụ sau:

| Công cụ | Bắt buộc | Mô tả |
|------|----------|-------------|
| Tài khoản Claude | Có | Gói Pro, Team, hoặc Enterprise (có hỗ trợ tính năng Skills). |
| Python 3.9+ | Có | Cần thiết để chạy các script lấy và phân tích dữ liệu cục bộ. |
| Thư viện `vnstock` | Có | Công cụ lấy dữ liệu thị trường chứng khoán Việt Nam miễn phí (từ TCBS, SSI, VND, v.v.). |

**Cài đặt thư viện Python:**

Mở terminal/command prompt và chạy lệnh sau để cài đặt các thư viện cần thiết:
```bash
pip install vnstock pandas numpy
```

---

## 2. Cài đặt Kỹ năng (Installation)

Bạn có hai cách để sử dụng bộ kỹ năng này: qua Claude Web App hoặc qua Claude Code chạy ở dưới máy (Local).

### Cách 1: Sử dụng qua Claude Web App (Khuyên dùng)

1. Tải xuống tệp `.skill` (định dạng ZIP) cho kỹ năng bạn muốn từ thư mục [`skill-packages/`](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skill-packages).
2. Mở Claude trên trình duyệt web và điều hướng tới **Settings > Skills**.
3. Upload tệp `.skill` vừa tải về.
4. Kỹ năng sẽ tự động kích hoạt trong các cuộc hội thoại mới của bạn.

> Xem thêm bài viết [Ra mắt tính năng Skills](https://www.anthropic.com/news/skills) từ Anthropic để hiểu tổng quan.
{: .note }

### Cách 2: Sử dụng qua Claude Code (Desktop / CLI)

1. Clone repository về máy tính:
   ```bash
   git clone https://github.com/xonevn-ai/xone-trading-skills.git
   cd xone-trading-skills
   ```
2. Copy thư mục kỹ năng mong muốn vào thư mục Skills của Claude Code (Tìm đường dẫn qua Claude Code -> Settings -> Skills -> Open Skills Folder).
3. Khởi động lại Claude Code để hệ thống nhận diện kỹ năng mới.

---

## 3. Chạy thử Kỹ năng đầu tiên: Báo cáo Đầu ngày (vn-daily-brief)

`vn-daily-brief` là kỹ năng dễ trải nghiệm nhất để thấy được sức mạnh tổng hợp của hệ sinh thái `vn-*`. Kỹ năng này đóng vai trò như một "trợ lý" chuẩn bị mọi dữ liệu định lượng trước giờ mở cửa.

### Bước 1: Chuẩn bị dữ liệu OHLCV
Trước tiên, bạn cần có dữ liệu nến (OHLCV) của thị trường. Nếu bạn chưa có, kỹ năng `vn-data-fetcher` sẽ giúp bạn lấy dữ liệu này. Hãy yêu cầu Claude:
> *"Hãy dùng vn-data-fetcher lấy dữ liệu OHLCV 3 tháng gần nhất cho các mã FPT, VIC, HPG."*

### Bước 2: Kích hoạt VN Daily Brief
Sau khi có dữ liệu, hãy ra lệnh cho Claude:
> *"Hãy chạy quy trình vn-daily-brief cho tôi."*

### Bước 3: Quan sát Claude làm việc
Claude sẽ tự động thực hiện các bước sau:
1. **Phân tích Ngành (Sector Analysis):** Đọc các file OHLCV để xác định ngành nào đang hút dòng tiền.
2. **Rà soát Room Ngoại:** Quét thay đổi room của khối ngoại từ ngày hôm trước.
3. **Cập nhật Danh mục:** Xem xét P&L của các vị thế đang mở.
4. **Tổng hợp Báo cáo:** Render ra một bản báo cáo Markdown sạch sẽ, dễ đọc ngay trên giao diện chat.

### Bước 4 (Tùy chọn): Kết hợp Tin tức
Bạn có thể nối tiếp bằng câu lệnh:
> *"Hãy quét tin tức CafeF sáng nay và bổ sung vào báo cáo trên."*
Claude sẽ sử dụng kỹ năng `vn-news-analyst` để hoàn thiện bản tin sáng cho bạn.

---

## 4. Xử lý Sự cố (Troubleshooting)

### Kỹ năng không phản hồi hoặc không nhận diện
| Nguyên nhân | Cách khắc phục |
|-------|-----|
| Quên cài `vnstock` | Hãy chắc chắn bạn đã chạy `pip install vnstock`. Nếu hệ thống báo lỗi không tìm thấy module, hãy kiểm tra lại môi trường Python (Virtual Environment). |
| Sai đường dẫn state | Một số kỹ năng yêu cầu đọc/ghi dữ liệu vào thư mục `state/`. Hãy đảm bảo bạn đang chạy Claude Code ở ngay thư mục gốc của repository. |

### Lỗi hiển thị Tiếng Việt
Nếu Terminal hoặc PowerShell của bạn bị lỗi font chữ (ví dụ xuất hiện các ký tự `\xe2`), hãy ép buộc Python sử dụng mã hóa UTF-8 bằng cách thiết lập biến môi trường trước khi chạy:
```bash
# Trên Windows PowerShell
$env:PYTHONIOENCODING="utf-8"

# Trên Mac/Linux
export PYTHONIOENCODING=utf-8
```

> **Mẹo nhỏ:** Hãy đọc tệp `README.vi.md` ở thư mục gốc để nắm được bức tranh tổng thể về kiến trúc và vòng đời giao dịch (Plan → Trade → Record → Review) mà bộ công cụ này hỗ trợ!
{: .tip }
