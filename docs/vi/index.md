---
layout: default
title: Tiếng Việt
nav_order: 1
has_children: true
permalink: /vi/
---

# Kỹ năng Giao dịch Claude (Vietnam Edition)
{: .no_toc }

<div class="hero">
  <p class="hero-mantra">Nâng tầm Nhà đầu tư Cá nhân - Cùng nhau Phát triển</p>
  <p class="hero-tagline">Bộ kỹ năng phân tích, lọc cổ phiếu và giao dịch thị trường Việt Nam được hỗ trợ bởi Claude</p>
</div>

## Bộ Kỹ năng Giao dịch Claude là gì?

Xone Trading Skills là bộ sưu tập các **Kỹ năng Claude** được thiết kế đặc biệt cho các nhà đầu tư chứng khoán. Phiên bản này tập trung vào thị trường chứng khoán Việt Nam (`vn-*`), tích hợp các lời nhắc (prompts), kiến thức chuyên môn, và các kịch bản phụ trợ để Claude có thể giúp bạn phân tích thị trường, lọc cổ phiếu, kiểm chứng chiến lược và quản lý danh mục đầu tư.

Hãy yêu cầu bằng ngôn ngữ tự nhiên, và nhận lại các báo cáo cấu trúc, dễ hiểu với các thông tin hành động (actionable insights) dưới định dạng Markdown và JSON.

<div class="category-cards">
  <div class="category-card">
    <h3>Lọc Cổ phiếu (Screening)</h3>
    <p>CANSLIM, VCP, Phân tích KQKD (Earnings) và Cổ tức. Các phương pháp đầu tư quốc tế được chuẩn hóa và điều chỉnh riêng cho thị trường Việt Nam (tích hợp thanh khoản, room ngoại).</p>
  </div>
  <div class="category-card">
    <h3>Phân tích Thị trường</h3>
    <p>Luân chuyển dòng tiền ngành, phân tích tin tức và theo dõi room ngoại. Đánh giá sức khỏe tổng thể của thị trường và định hướng dòng tiền thông minh.</p>
  </div>
  <div class="category-card">
    <h3>Lập kế hoạch Giao dịch</h3>
    <p>Lập kế hoạch mua Breakout/Pullback, phòng vệ phái sinh (VN30), định cỡ vị thế (Position Sizing) và kiểm tra danh sách cắt margin (Q-rated) từ các CTCK.</p>
  </div>
  <div class="category-card">
    <h3>Quản trị Danh mục</h3>
    <p>Ghi chép Nhật ký giao dịch (Trading Journal), quản lý P&L, tính toán thuế phí (so sánh các CTCK) và tổng hợp Báo cáo Đầu ngày (Morning Routine).</p>
  </div>
</div>

---

## Cách thức Hoạt động

<div class="steps">
  <div class="step">
    <span class="step-number">1</span>
    <h4>Cài đặt</h4>
    <p>Tải tệp <code>.skill</code> lên Claude Web App, hoặc sao chép thư mục kỹ năng vào Claude Code trên máy tính của bạn.</p>
  </div>
  <div class="step">
    <span class="step-number">2</span>
    <h4>Yêu cầu</h4>
    <p>Giao tiếp với Claude bằng Tiếng Việt tự nhiên để yêu cầu phân tích dữ liệu OHLCV, chạy bộ lọc, hoặc xem báo cáo.</p>
  </div>
  <div class="step">
    <span class="step-number">3</span>
    <h4>Nhận Báo cáo</h4>
    <p>Nhận các báo cáo Markdown định dạng đẹp mắt kèm dữ liệu JSON thô đã được xử lý sẵn sàng cho việc ra quyết định.</p>
  </div>
</div>

---

## Các Kỹ năng Nổi bật

| Kỹ năng | Điểm nhấn | API / Dữ liệu |
|-------|-----------|-----|
| [Báo cáo Đầu ngày (Daily Brief)]({{ '/vi/skills/vn-daily-brief/' | relative_url }}) | Tự động hóa hoàn toàn quy trình phân tích buổi sáng: Luân chuyển ngành, Thay đổi Room ngoại, P&L Danh mục. | Không yêu cầu |
| [Lọc CANSLIM VN]({{ '/vi/skills/vn-canslim-screener/' | relative_url }}) | Chấm điểm CANSLIM điều chỉnh cho Việt Nam (Dùng Room ngoại đại diện cho chữ I, dùng ngành dẫn dắt cho chữ L). | `vnstock` |
| [Phân tích KQKD (Earnings)]({{ '/vi/skills/vn-earnings-analyzer/' | relative_url }}) | Chấm điểm phản ứng giá ngày ra BCTC (Gap up, Khối lượng đột biến, EPS Surprise) để tìm siêu cổ phiếu. | `vnstock` |
| [Kế hoạch Breakout]({{ '/vi/skills/vn-breakout-trade-planner/' | relative_url }}) | Lên kế hoạch mua chi tiết, tự động kiểm tra Room ngoại và Thanh khoản để đảm bảo an toàn. | `vnstock` |

Bạn có thể xem đầy đủ danh sách tại [Thư mục Kỹ năng (Skill Catalog)]({{ '/vi/skill-catalog/' | relative_url }}).

---

## Bắt đầu

Nếu bạn là người mới? Hãy truy cập [Bắt đầu Nhanh (Getting Started)]({{ '/vi/getting-started/' | relative_url }}) để xem hướng dẫn cài đặt, thiết lập thư viện và chạy kỹ năng đầu tiên.
