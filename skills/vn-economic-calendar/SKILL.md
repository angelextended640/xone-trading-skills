---
name: vn-economic-calendar
description: Lịch sự kiện vĩ mô Việt Nam — quyết định lãi suất SBV (định kỳ và bất thường), công bố GDP/CPI/FDI/xuất nhập khẩu của GSO, ngày họp FOMC ảnh hưởng USD/VND. Bao gồm calendar template + impact patterns + nguồn chính thức. Kích hoạt khi user hỏi "có sự kiện gì sắp tới", "khi nào SBV họp", "CPI tháng này", "FOMC ảnh hưởng VN-Index". Vietnam macro events calendar — SBV rate decisions, GSO releases (GDP/CPI/FDI/trade), FOMC dates that move USDVND. Knowledge-only reference for event-driven swing trading.
---

# VN Economic Calendar — Lịch sự kiện vĩ mô Việt Nam

## Tổng quan

Skill tham chiếu **knowledge-only** liệt kê các sự kiện vĩ mô có khả năng tác động lên TTCK Việt Nam:

- **Lịch SBV** — quyết định lãi suất định kỳ + chính sách OMO / tỷ giá
- **Lịch GSO** — GDP (quý), CPI (tháng), FDI (tháng), xuất nhập khẩu (tháng)
- **Lịch quốc tế** — FOMC, ECB, BOJ, dữ liệu Mỹ ảnh hưởng EM / USDVND
- **Lịch nội bộ thị trường** — ngày chốt quyền, ngày họp ĐHCĐ blue-chip, kết quả kinh doanh quý
- **Pattern theo mùa** — chu kỳ vốn cuối tháng / quý, hiệu ứng Tết, Quarter-end

## Khi nào dùng

- Bắt đầu tuần / tháng — review sự kiện sắp tới
- User hỏi "có gì quan trọng tuần này?" / "SBV họp ngày nào?"
- Trước khi đặt lệnh — kiểm tra rủi ro sự kiện (event risk)
- Combine với `vn-news-analyst` (lịch + tin tức cụ thể)

## Cách dùng

Đây là **knowledge-only skill** — không có script. User mở SKILL.md và các file trong `references/` để xem:

- `references/vn_macro_event_schedule.md` — lịch sự kiện theo tháng + nguồn
- `references/vn_event_impact_window.md` — cửa sổ tác động của mỗi loại sự kiện
- `references/vn_seasonal_patterns.md` — pattern theo mùa và chu kỳ vốn

Khi cần date cụ thể: user query WebSearch site:sbv.gov.vn / site:gso.gov.vn / fomc dates.

## Quy trình review weekly

1. **Sáng thứ 2:** Đọc `vn_macro_event_schedule.md` để xác định sự kiện trong tuần.
2. **Nếu có sự kiện trọng yếu (SBV / CPI / FOMC):**
   - Reduce position sizing trong ngày sự kiện (tránh gap risk)
   - Đánh dấu trade plan có exit pre-event nếu cần
3. **Sau sự kiện:** Trigger `vn-news-analyst` để phân tích phản ứng và update trade plan.

## Resources

- `references/vn_macro_event_schedule.md` — Lịch sự kiện
- `references/vn_event_impact_window.md` — Cửa sổ tác động
- `references/vn_seasonal_patterns.md` — Pattern mùa vụ
- Cross-references:
  - `skills/vn-news-analyst/references/vn_event_impact_patterns.md` — Mapping sự kiện → mã
  - `skills/vn-market-mechanics/references/vn_trading_rules.md` — Lịch nghỉ lễ TTCK

## Nguyên tắc

1. **Lịch là khung sườn, không phải predictions** — Skill này nói "ngày X có FOMC", không nói "FOMC sẽ tăng lãi suất".
2. **Cập nhật từ nguồn chính thức** — SBV, GSO publish lịch hàng tháng. Đừng trust lịch cached.
3. **Cảnh báo event risk** — Trước sự kiện lớn, reduce risk hoặc avoid new entries.
4. **Pattern không phải prediction** — Quarter-end vốn flow là tendency, không phải certainty.
