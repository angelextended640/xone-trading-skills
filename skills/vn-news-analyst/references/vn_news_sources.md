# Nguồn tin TTCK Việt Nam — Bảng phân tầng

**Last updated:** 2026-05-13

Phân tầng nguồn tin để chọn ưu tiên khi WebSearch + WebFetch. Càng cao tầng càng đáng tin và nên trích dẫn trước.

## Tier 1 — Nguồn chính (luôn ưu tiên)

| Nguồn | URL gốc | Đặc điểm |
| --- | --- | --- |
| **CafeF** | https://cafef.vn/ | Báo CK lớn nhất VN. Bao quát đầy đủ: thị trường, macro, công ty, ngành. Update nhanh. |
| **Vietstock** | https://vietstock.vn/ | Báo CK chuyên sâu. Có data và phân tích kỹ thuật / cơ bản. |
| **NDH (Người Đồng Hành)** | https://ndh.vn/ | Báo CK chuyên môn cao. Bài phân tích sâu sắc. |
| **Báo Đầu Tư** | https://baodautu.vn/ | Báo nhà nước về đầu tư, doanh nghiệp. Tin chính sách / quy định đáng tin. |

**Search syntax:**
```
site:cafef.vn <keywords>
site:vietstock.vn <keywords>
site:ndh.vn <keywords>
site:baodautu.vn <keywords>
```

## Tier 2 — Nguồn bổ sung

| Nguồn | URL | Phù hợp cho |
| --- | --- | --- |
| **VnExpress Kinh doanh** | https://vnexpress.net/kinh-doanh | Tin macro, doanh nghiệp lớn — phổ thông |
| **VietnamFinance** | https://vietnamfinance.vn/ | Tin ngân hàng, tài chính, BĐS |
| **VnEconomy** | https://vneconomy.vn/ | Tin kinh tế vĩ mô, chính sách |
| **Doanh Nhân Sài Gòn Online** | https://doanhnhansaigon.vn/ | Tin doanh nghiệp |
| **The Saigon Times** | https://thesaigontimes.vn/ | English nguồn — đôi khi có góc nhìn từ tổ chức quốc tế |

## Tier 3 — Tham khảo cẩn trọng

| Nguồn | Đặc điểm | Cảnh báo |
| --- | --- | --- |
| **F319, F247 (forum)** | Sôi nổi, theo sát phiên | **Tin đồn nhiều**, cần xác minh chéo. KHÔNG trích dẫn trong report. |
| **Facebook groups CK** | Update nhanh tin chiều phiên | Tương tự — chỉ dùng để xác định buzz, không phải tin chính |
| **YouTube chứng khoán** | Phân tích từ một số chuyên gia | Cá nhân — kiểm tra credentials trước khi trích |

## Nguồn chính thức (cho macro / chính sách)

| Tổ chức | URL | Loại thông tin |
| --- | --- | --- |
| **SBV** (Ngân hàng Nhà nước) | https://www.sbv.gov.vn/ | Quyết định lãi suất, OMO, tỷ giá tham chiếu, dự trữ ngoại hối |
| **UBCKNN** | https://www.ssc.gov.vn/ | Quy định CK, danh sách cảnh báo, cấp phép CTCK |
| **HOSE** | https://www.hsx.vn/ | Công bố HOSE, danh sách cảnh báo, kiểm soát |
| **HNX** | https://www.hnx.vn/ | Công bố HNX, niêm yết mới |
| **Tổng cục Thống kê** (GSO) | https://www.gso.gov.vn/ | GDP, CPI, FDI, xuất nhập khẩu |
| **Bộ Tài chính** | https://www.mof.gov.vn/ | Chính sách thuế, ngân sách |

## Search query templates

### Tin general hôm nay
```
"thị trường chứng khoán" OR "VN-Index" OR "HOSE" date:1d
```

### Tin lãi suất SBV
```
"SBV" OR "Ngân hàng Nhà nước" "lãi suất" date:7d
```

### Tin về mã cụ thể (vd VIC)
```
"VIC" OR "Vingroup" site:cafef.vn OR site:vietstock.vn date:7d
```

### Tin foreign flow
```
"khối ngoại" OR "nhà đầu tư nước ngoài" "mua ròng" OR "bán ròng" date:1d
```

### Tin ngành (vd Banking)
```
"ngân hàng" "lợi nhuận" OR "tăng trưởng tín dụng" date:7d
```

### Tin macro
```
"CPI" OR "GDP" OR "FDI" "Việt Nam" date:30d
```

## Quy ước trích dẫn

Khi đưa vào report, format trích dẫn:
```
**Source:** [Tên nguồn] — [Tiêu đề bài] — YYYY-MM-DD
**URL:** [link]
```

Ví dụ:
```
**Source:** CafeF — "SBV giữ nguyên lãi suất điều hành, tăng cường thanh khoản hệ thống" — 2026-05-13
**URL:** https://cafef.vn/sbv-giu-nguyen-lai-suat-...
```

## Khi không tìm thấy tin

Nếu sau 5-10 queries vẫn không có tin lớn, **không tự bịa**. Trả về:
```
## Today's News Brief
**Status:** No major market-moving news identified in the past N hours.
**Quiet day note:** Markets appear in a normal trading pattern. Monitor for late-session announcements.
```
