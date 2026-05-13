# Lịch sự kiện vĩ mô Việt Nam

**Last updated:** 2026-05-13
**Mục đích:** Khung sườn các sự kiện vĩ mô định kỳ ảnh hưởng TTCK VN. Cập nhật từ nguồn chính thức trước mỗi sự kiện.

## Lịch SBV (Ngân hàng Nhà nước Việt Nam)

### Định kỳ

| Sự kiện | Tần suất | Ngày phổ biến |
| --- | --- | --- |
| **Quyết định điều hành chính sách tiền tệ** | Bất định | Thông thường công bố khi cần (không có lịch FOMC như Mỹ) |
| **Công bố tỷ giá tham chiếu USDVND** | Hàng ngày | Sáng phiên (≤08:30) |
| **Báo cáo tăng trưởng tín dụng** | Hàng tháng | Cuối tháng |
| **Họp Hội đồng tư vấn Chính sách tiền tệ** | Hàng quý | Thường tháng 3, 6, 9, 12 |
| **Bơm / rút thanh khoản OMO** | Hàng ngày | Phiên sáng (10:00-11:30) |

**Nguồn:** https://www.sbv.gov.vn/

### Sự kiện bất thường (cần WebSearch để check)

- Điều chỉnh lãi suất điều hành (refinancing, rediscount)
- Nới / siết room tăng trưởng tín dụng cho các bank
- Ban hành thông tư mới về margin, room ngoại, KRX

**Cách track:** WebSearch `site:sbv.gov.vn` thường xuyên + theo dõi tin Tier 1 (`vn-news-analyst`).

## Lịch GSO (Tổng cục Thống kê)

### Định kỳ

| Sự kiện | Tần suất | Ngày publish | Tác động ngắn hạn |
| --- | --- | --- | --- |
| **CPI** (Consumer Price Index) | Hàng tháng | Khoảng ngày **29-30** của tháng tham chiếu | High — quyết định kỳ vọng lãi suất SBV |
| **IIP** (Industrial Production Index) | Hàng tháng | Khoảng ngày **29-30** | Medium — chu kỳ ngành công nghiệp |
| **Xuất nhập khẩu** | Hàng tháng | Đầu tháng kế tiếp (ngày 1-10) | Medium — affect dệt may, thủy sản, thép |
| **FDI** (đăng ký + giải ngân) | Hàng tháng | Cuối tháng | Medium — KCN, cảng, hạ tầng |
| **GDP** | Hàng quý | Cuối tháng cuối quý (31/3, 30/6, 30/9, 30/12) | Very High — tâm điểm tuần |
| **Bán lẻ hàng hóa, dịch vụ** | Hàng tháng | Cuối tháng | Medium — consumer stocks |

**Nguồn:** https://www.gso.gov.vn/

## Lịch quốc tế ảnh hưởng VN-Index

### FOMC (Cục Dự trữ Liên bang Mỹ)

| Tháng họp | Ngày họp |
| --- | --- |
| Tháng 1 | Cuối tháng (28-29) |
| Tháng 3 | Trung tháng (18-19) |
| Tháng 5 | Đầu tháng (6-7) |
| Tháng 6 | Trung tháng (17-18) |
| Tháng 7 | Cuối tháng (29-30) |
| Tháng 9 | Trung tháng (16-17) |
| Tháng 11 | Đầu tháng (4-5) |
| Tháng 12 | Trung tháng (16-17) |

(Lịch chính xác: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm — verify before each cycle)

**Tác động VN:** FOMC quyết định ảnh hưởng:
- USDVND (Fed hawkish → USDVND tăng → SBV áp lực can thiệp)
- Dòng vốn EM (Fed dovish → vốn nước ngoài đổ về EM, thuận lợi VN)
- Sentiment toàn cầu

### Dữ liệu Mỹ quan trọng

| Sự kiện | Lịch publish | Tác động |
| --- | --- | --- |
| **Non-Farm Payrolls** | Thứ 6 đầu tháng | Cao — sentiment EM, USD |
| **CPI Mỹ** | Trung tháng (10-15) | Cao — định kỳ Fed |
| **PCE** (Fed's preferred inflation) | Cuối tháng | Cao |
| **ISM Manufacturing PMI** | Đầu tháng | Trung |
| **Retail Sales** | Trung tháng | Trung |
| **GDP advance estimate** | Cuối tháng (sau quý) | Cao |

### ECB / BOJ

- **ECB:** Họp khoảng 6 tuần/lần. Ảnh hưởng EUR/USD → gián tiếp USDVND.
- **BOJ:** Họp 8 lần/năm. Quan trọng nhất là quyết định YCC (Yield Curve Control). 2024: bỏ YCC tạo biến động lớn JPY → ảnh hưởng EM.

## Lịch nội bộ thị trường VN

### Mùa kết quả kinh doanh

| Quý | Tháng công bố KQKD | Highlights |
| --- | --- | --- |
| Q4 năm trước | Tháng 1-2 | + Tổng kết năm, kế hoạch năm mới |
| Q1 | Tháng 4 | Đặt kỳ vọng full-year |
| Q2 | Tháng 7-8 | Mid-year check, ĐHCĐ mid-term |
| Q3 | Tháng 10-11 | Setup quý cuối |

### Sự kiện chốt quyền (ex-rights date)

- **Cổ tức tiền mặt:** Giá giảm theo ratio tại ngày ex-date
- **Cổ tức bằng cổ phiếu:** Giá điều chỉnh, số CP tăng
- **Phát hành thêm:** Cần theo dõi pha loãng

Track per-symbol qua CTCK app hoặc `vn-data-fetcher` (vnstock có dividend schedule).

### ĐHCĐ thường niên (AGM)

- **Tháng 4-6** là peak AGM season
- Blue-chip AGM thường tiết lộ kế hoạch năm + cổ tức → tác động giá ngắn hạn

## Lịch nghỉ lễ TTCK 2026 (gợi ý — verify với HOSE)

| Sự kiện | Ngày | Nghỉ giao dịch |
| --- | --- | --- |
| Tết Dương lịch | 01/01 | 1 ngày |
| Tết Nguyên đán | Khoảng 16-22/02 | ~5-7 ngày |
| Giỗ Tổ Hùng Vương | 10/3 âm lịch (~16/04) | 1 ngày |
| Giải phóng + Quốc tế Lao động | 30/04 + 01/05 | 2 ngày |
| Quốc khánh | 02/09 | 1 ngày |

Verify exact dates qua HOSE: https://www.hsx.vn/

**Lưu ý Tết:** Tuần sau Tết thường thanh khoản thấp; tuần trước Tết thường rút vốn / chốt lãi.

## Workflow weekly review

### Mỗi sáng thứ 2

1. Đọc `vn_macro_event_schedule.md` để xác định:
   - Sự kiện SBV trong tuần?
   - Công bố GSO cuối tuần (CPI / GDP)?
   - FOMC tuần này?
2. Đánh dấu các ngày "event risk":
   - Reduce position sizing trên ngày đó
   - Cân nhắc exit pre-event hoặc giảm 50% size
3. Trigger `vn-news-analyst` để phân tích sentiment hiện tại

### Sau mỗi sự kiện

1. Trigger `vn-news-analyst` để phân tích phản ứng
2. Update trade plans:
   - Tighten stops nếu market reaction phù hợp với expectation
   - Cancel pending breakouts nếu sentiment đảo chiều

## Nguồn

- **SBV:** https://www.sbv.gov.vn/
- **GSO:** https://www.gso.gov.vn/
- **HOSE:** https://www.hsx.vn/ (lịch nghỉ, công bố)
- **HNX:** https://www.hnx.vn/
- **FOMC:** https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
- **Bộ Tài chính:** https://www.mof.gov.vn/
- **UBCKNN:** https://www.ssc.gov.vn/
