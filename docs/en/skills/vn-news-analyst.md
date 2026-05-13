---
layout: default
title: "Vn News Analyst"
grand_parent: English
parent: Skill Guides
nav_order: 11
permalink: /en/skills/vn-news-analyst/
---

# Vn News Analyst
{: .no_toc }

Phân tích tin tức TTCK Việt Nam qua WebSearch và WebFetch. Nguồn ưu tiên CafeF, Vietstock, NDH, VnExpress Kinh doanh, VietnamFinance. Phân loại tin theo monetary policy / regulation / sector / company / macro, đánh giá tác động lên VN-Index, đề xuất các mã hưởng lợi / chịu tác động. Kích hoạt khi user hỏi "tin tức thị trường VN", "có gì mới hôm nay", "ảnh hưởng đến cổ phiếu nào", "SBV làm gì", "nhà đầu tư nước ngoài". Vietnam stock market news analyst — categorise, score impact, surface affected tickers. Sources: CafeF, Vietstock, NDH, VnExpress Kinh doanh.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/vn-news-analyst){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VN News Analyst — Phân tích tin tức TTCK Việt Nam

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

```bash
site:cafef.vn <keywords>
   site:vietstock.vn <keywords>
   site:ndh.vn <keywords>
   site:vnexpress.net kinh-doanh <keywords>
```

---

## 4. Workflow

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

---

## 5. Resources

**References:**

- `skills/vn-news-analyst/references/vn_event_impact_patterns.md`
- `skills/vn-news-analyst/references/vn_news_sources.md`
