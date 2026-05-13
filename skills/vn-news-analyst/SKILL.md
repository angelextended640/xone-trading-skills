---
name: vn-news-analyst
description: "Phân tích tin tức TTCK Việt Nam qua WebSearch và WebFetch. Nguồn ưu tiên CafeF, Vietstock, NDH, VnExpress Kinh doanh, VietnamFinance. Phân loại tin theo monetary policy / regulation / sector / company / macro, đánh giá tác động lên VN-Index, đề xuất các mã hưởng lợi / chịu tác động. Kích hoạt khi user hỏi 'tin tức thị trường VN', 'có gì mới hôm nay', 'ảnh hưởng đến cổ phiếu nào', 'SBV làm gì', 'nhà đầu tư nước ngoài'. Vietnam stock market news analyst — categorise, score impact, surface affected tickers. Sources: CafeF, Vietstock, NDH, VnExpress Kinh doanh."
---

# VN News Analyst — Phân tích tin tức TTCK Việt Nam

## Tổng quan

Quét, phân loại và đánh giá tác động của tin tức tài chính Việt Nam lên thị trường chứng khoán.
Tận dụng WebSearch + WebFetch để truy cập các nguồn tin uy tín nhất, sau đó trích xuất:

- **Tóm tắt sự kiện** (3-5 câu)
- **Phân loại** theo 6 nhóm: monetary policy / regulation / sector / company / macro / sentiment
- **Tác động dự kiến** lên VN-Index (mạnh tăng / nhẹ tăng / trung lập / nhẹ giảm / mạnh giảm)
- **Mã hưởng lợi và mã chịu tác động** (3-5 mã mỗi nhóm)
- **Mức độ ưu tiên monitoring** (urgent / high / medium / low)

## Khi nào dùng

- User hỏi "có tin gì mới hôm nay?" / "tin SBV mới ra ảnh hưởng gì?" / "tại sao VN-Index giảm/tăng?"
- Bắt đầu phiên — quick news scan trước khi đặt lệnh
- Khi cần context cho `vn-sector-analyst` (ngành nào đang trending vì lý do gì?)
- Khi cần background cho `vn-breakout-trade-planner` (mã đang lên do tin nào?)
- Theo dõi sự kiện macro: quyết định lãi suất SBV, công bố GDP / CPI / FDI

## Điều kiện tiên quyết

- WebSearch và WebFetch tools (built-in trong Claude Code)
- Không cần API key cho data scrape
- Tham chiếu: `references/vn_news_sources.md`, `references/vn_event_impact_patterns.md`

## Workflow

### Phase 1: Thu thập tin

1. **Xác định scope từ user query**:
   - "tin hôm nay" → past 24h
   - "tuần này" → past 7d
   - Tin về một mã cụ thể → search trực tiếp ticker
   - Tin về một ngành → keyword theo ngành (xem `references/vn_news_sources.md`)

2. **WebSearch với queries ưu tiên nguồn Tier 1**:
   ```
   site:cafef.vn <keywords>
   site:vietstock.vn <keywords>
   site:ndh.vn <keywords>
   site:vnexpress.net kinh-doanh <keywords>
   ```

3. **Chọn 5-10 bài viết** có:
   - Source ở Tier 1 hoặc Tier 2 (xem references)
   - Đăng trong scope thời gian
   - Tiêu đề liên quan rõ ràng đến thị trường / vĩ mô / chính sách

4. **WebFetch nội dung** chi tiết các bài quan trọng nhất.

### Phase 2: Phân loại và đánh giá

Cho mỗi tin, xác định:

#### Category (1 trong 6):

| Category | Đặc trưng | Tác động điển hình |
| --- | --- | --- |
| **Monetary Policy** | SBV, lãi suất, OMO, tỷ giá, thanh khoản | Banking, BĐS, toàn thị trường |
| **Regulation** | UBCKNN, KRX, T+1, margin rules, thuế CK | Toàn thị trường, ngân hàng, CTCK |
| **Sector** | Tin ngành: BĐS, dầu khí, ngân hàng, công nghệ | Mã trong ngành |
| **Company** | Công bố cá nhân: KQKD, M&A, cổ tức, scandal | Mã cụ thể |
| **Macro** | GDP, CPI, FDI, xuất nhập khẩu, FED, USDVND | Toàn thị trường, ngành xuất khẩu |
| **Sentiment** | Khối ngoại, margin debt, F0, tin đồn | Beta cao, mã đầu cơ |

#### Impact level:

| Mức | Ký hiệu | Mô tả |
| --- | --- | --- |
| Strong Positive | `++` | VN-Index có thể +1.5%+ trên tin |
| Mild Positive | `+` | +0.3 – 1.5% |
| Neutral | `0` | < 0.3% |
| Mild Negative | `-` | −0.3 – −1.5% |
| Strong Negative | `--` | < −1.5% |

#### Priority:

- **Urgent**: Tin mới ra trong giờ giao dịch, có khả năng ảnh hưởng phiên hôm nay/mai
- **High**: Tin macro / chính sách trong tuần
- **Medium**: Tin ngành / công ty lớn
- **Low**: Tin bổ sung / context

### Phase 3: Mapping mã hưởng lợi / chịu tác động

Tham khảo `references/vn_event_impact_patterns.md` để xác định:

- **Tin tăng lãi suất SBV** → Banking (BID, VCB) hưởng lợi NIM; BĐS (VIC, NVL) chịu ảnh hưởng
- **Tin nới room ngoại** → mã đang được nước ngoài quan tâm (FPT, MWG, PNJ) hưởng lợi
- **Tin căng thẳng địa chính trị** → Năng lượng (GAS, PLX), thép (HPG, HSG) tăng
- **Tin nới margin** → CTCK (SSI, VCI, HCM) hưởng lợi trước

Chi tiết bảng tác động xem reference file.

### Phase 4: Generate report

Output Markdown report theo template:

```markdown
# VN Market News Brief
**As of:** YYYY-MM-DD HH:MM
**Scope:** [past N hours/days]
**VN-Index expected impact:** [overall +/-/neutral]

## Top Stories (priority: urgent + high)

### 1. [Headline 1] (Category: Monetary Policy / High / ++)
**Source:** CafeF / 2026-05-13
**Summary:** ...
**Affected tickers (positive):** VCB, BID, CTG (Banking — NIM rises)
**Affected tickers (negative):** VIC, NVL, KDH (Real Estate — funding costs rise)
**Action consideration:** Monitor banking sector breakout next 2-3 sessions.

### 2. ...

## Sector Tilt
- **Banking:** mild positive overall
- **Real Estate:** mild negative
- **Materials:** neutral
- ...

## Foreign Flow Note (nếu có)
[Tin về khối ngoại mua/bán]

## Monitoring Points
- [Sự kiện sắp tới cần theo dõi]
```

Lưu vào `reports/vn_news_brief_YYYY-MM-DD_HHMMSS.md`.

## Resources

- `references/vn_news_sources.md` — Bảng nguồn Tier 1/2/3 với keyword search tips
- `references/vn_event_impact_patterns.md` — Bảng tác động sự kiện → ngành / mã

## Nguyên tắc

1. **Trích dẫn nguồn rõ ràng** — mỗi tin phải có source name + URL + ngày đăng. Tránh trộn các nguồn vào một paragraph.
2. **Ưu tiên Tier 1** — CafeF, Vietstock, NDH là nguồn cốt lõi. Tier 2 (VnExpress KD, VietnamFinance) bổ sung. Tránh tin đồn / forum.
3. **Đánh giá tác động có lý do** — Mỗi mã suggested phải có rationale rõ ràng (mechanism nào kết nối tin đến mã đó).
4. **Không khuyến nghị mua/bán cụ thể** — Output là phân tích tác động, **không phải** lời khuyên đầu tư. User tự quyết định.
5. **Cập nhật scope** — Mặc định 24h cho tin hàng ngày. Tin macro / chính sách lớn có thể mở rộng 7-14d.
6. **Cảnh báo khi không có tin lớn** — Đừng tự "phóng đại" tin nhỏ. Nếu thị trường ngày bình thường, nói rõ.
