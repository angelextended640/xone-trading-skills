# Xone Trading Skills — Bộ kỹ năng giao dịch CK Việt Nam

> 🇻🇳 **Trọng tâm chính:** Thị trường chứng khoán Việt Nam — HOSE / HNX / UPCOM.
> Thị trường quốc tế (US) chỉ giữ lại cho người dùng nâng cao.

Bộ "kỹ năng" (Claude Skills) hỗ trợ workflow giao dịch cho **nhà đầu tư cá nhân Việt Nam** có quỹ thời gian hạn chế. Mục tiêu là chuẩn hoá quy trình review thị trường, quản trị rủi ro, lập kế hoạch giao dịch, ghi nhật ký và cải tiến liên tục — **không** thay thế phán đoán của bạn, **không** đưa ra tín hiệu mua/bán.

Bản tiếng Anh: [`README.md`](README.md) — chủ yếu cho người dùng quốc tế / contributors.

---

## Mục lục

- [Tuyên bố miễn trừ trách nhiệm](#tuyên-bố-miễn-trừ-trách-nhiệm)
- [Đặc thù thị trường VN cần nhớ](#đặc-thù-thị-trường-vn-cần-nhớ)
- [Bộ skill Việt Nam](#bộ-skill-việt-nam-vn-)
- [Cài đặt nhanh](#cài-đặt-nhanh)
- [Workflow ngày điển hình (end-to-end)](#workflow-ngày-điển-hình-end-to-end)
- [Triết lý Core + Satellite](#triết-lý-core--satellite)
- [Cấu trúc project](#cấu-trúc-project)
- [Đóng góp](#đóng-góp)

---

## Tuyên bố miễn trừ trách nhiệm

Repo này phục vụ **mục đích giáo dục, nghiên cứu, và cải tiến quy trình giao dịch**. Đây **không phải** dịch vụ tư vấn đầu tư, không phải tín hiệu mua/bán, không phải broker, không phải tư vấn thuế hay pháp lý. Đầu tư có rủi ro, kể cả mất vốn. Mọi quyết định giao dịch, size lệnh, tuân thủ pháp lý/thuế là **trách nhiệm của bạn**.

Repo phát hành theo MIT License, **"AS IS"** — không bảo hành.

---

## Đặc thù thị trường VN cần nhớ

Nếu bạn quen với thị trường Mỹ qua sách / YouTube, các điểm sau **không giống** và phải nhớ:

| # | Đặc điểm VN | Khác Mỹ thế nào |
| --- | --- | --- |
| 1 | **Biên độ giá hàng phiên:** ±7% (HOSE), ±10% (HNX), ±15% (UPCOM) | Mỹ không có giới hạn intraday (chỉ circuit breaker toàn thị trường) |
| 2 | **Lô tròn 100 CP** | Mỹ giao dịch lẻ tự do từng cổ phiếu |
| 3 | **T+2.5 settlement** — CP mua hôm nay chỉ bán được **chiều T+2** | Mỹ T+1 (kể từ T+1 2024), giao dịch intraday tự do |
| 4 | **Không short cổ phiếu cơ sở** — chỉ short được phái sinh VN30 Futures | Mỹ short tự do (margin available) |
| 5 | **Phí + thuế ~0.4%/round-trip** (phí 0.15% × 2 + thuế bán 0.1%) | Mỹ broker phổ thông phí $0, thuế chỉ khi có lãi |
| 6 | **Room ngoại** (49% mặc định, 30% với ngân hàng) | Mỹ không có khái niệm tương đương |
| 7 | **Stop-loss "tự động" không tồn tại** ở hầu hết CTCK truyền thống | Mỹ broker đều hỗ trợ stop order |
| 8 | **Cổ phiếu cảnh báo / kiểm soát / hạn chế** bị giới hạn giao dịch | Mỹ không có hệ thống cảnh báo công khai theo dạng này |

Chi tiết đầy đủ tham khảo [`skills/vn-market-mechanics/references/`](skills/vn-market-mechanics/references/).

---

## Bộ skill Việt Nam (`vn-*`)

Đến nay đã có **21 skill `vn-*` đã hoạt động** bao trùm các nghiệp vụ từ dữ liệu, margin, tin tức đến screener và quản lý danh mục.

### Đã có sẵn ✅

| Skill | Mô tả | Subcommands | Tests |
| --- | --- | --- | --- |
| **`vn-market-mechanics`** | Tham chiếu chuẩn — biên độ ±7/10/15%, T+2.5, lô 100, phí, thuế, room ngoại. Mọi skill VN khác trích dẫn skill này. | (knowledge-only) | n/a |
| **`vn-position-sizer`** | Tính số CP cho lệnh mua. Lô 100, kiểm tra trần/sàn, phí 0.15% + thuế bán 0.1%, Fixed Fractional / ATR / Kelly. | 1 binary CLI | 35 |
| **`vn-data-fetcher`** | Wrapper CLI quanh `vnstock` — OHLCV, info công ty, lịch sử cổ tức, tỷ số tài chính, snapshot khối ngoại. Cache CSV local. `--fixture` mode cho test offline. | `ohlcv`, `info`, `dividends`, `fundamentals`, `foreign-flow` | 33 |
| **`vn-portfolio-manager`** | Quản lý danh mục VND. P&L sau phí và thuế, phân bổ ngành, cảnh báo concentration (10%/30%). Nhận giá từ vn-data-fetcher. | `add`, `remove`, `status`, `summary`, `closed` | 25 |
| **`vn-foreign-room-tracker`** | Theo dõi room ngoại theo ngày cho watchlist. Alert `full` / `released` / `spike_up` / `spike_down`. Append-only history. | `record`, `report`, `history` | 27 |
| **`vn-sector-analyst`** | Phân tích rotation theo ngành VN-Index. Mapping ~80 mã, 11 ngành. Return 5D/20D/60D, RS vs VN-Index, regime hint. | 1 binary CLI | 23 |
| **`vn-breakout-trade-planner`** | Lập trade plan long với guardrails VN: pivot/stop/R-multiple targets, T+2.5 calendar, tùy chọn ngữ cảnh sector + room. | 1 binary CLI | 28 |
| **`vn-tax-fee-calculator`** | Tính chi tiết phí broker theo CTCK + thuế bán 0.1% + thuế cổ tức 5% + lưu ký + ứng trước. So sánh net return giữa 10 CTCK. | `trade`, `compare`, `dividend`, `monthly` | 25 |
| **`vn-news-analyst`** | Phân tích tin tức TTCK VN qua WebSearch (CafeF, Vietstock, NDH). Categorise theo monetary policy / regulation / sector. Mapping tin → mã hưởng lợi / chịu tác động. | (knowledge + workflow) | n/a |
| **`vn-vcp-screener`** | Sàng lọc VCP (Mark Minervini) cho cổ phiếu VN, hiệu chỉnh cho biên độ ±7% HOSE. Phát hiện contraction liên tiếp, depth giảm dần, volume dry-up. Grade A/B/C. | 1 binary CLI | 18 |
| **`vn-pullback-screener`** | Sàng lọc cổ phiếu pullback đẹp về MA20/MA50, RSI 35-50, volume dry-up. Entry style ít rủi ro hơn breakout, phù hợp T+2.5. | 1 binary CLI | 18 |
| **`vn-economic-calendar`** | Lịch sự kiện macro VN: SBV, GSO (CPI/GDP/FDI), FOMC ảnh hưởng USDVND, ex-rights / AGM season, pattern Tết / quarter-end. | (knowledge-only) | n/a |
| **`vn-dividend-screener`** | Sàng lọc cổ phiếu cổ tức bền vững cho Core portfolio. Yield + payout sustainability + 3y dividend growth + ROE/D/E quality + EPS trajectory. Phát hiện yield trap (yield cao + EPS sụp đổ → auto-reject). | 1 binary CLI | 26 |
| **`vn30-derivatives-planner`** | Phái sinh VN30 Futures — `roll` (lịch 3rd-Thursday + basis), `hedge` (số contract theo beta), `plan` (full short/long trade plan với IM check), `cost` (so sánh 10 CTCK). T+0 settlement, không thuế bán. **Công cụ short hợp pháp duy nhất ở VN.** | `roll`, `hedge`, `plan`, `cost` | 39 |
| **`vn-trader-memory`** | Vòng lặp Plan → Trade → Record → Review cho VN trader. Đăng ký thesis từ `vn-*screener`, lifecycle IDEA→ENTRY_READY→ACTIVE→CLOSED, attach kết quả `vn-position-sizer`, đóng vị thế với P&L gross+phí+thuế+net (VND), postmortem MAE/MFE qua vnstock (loại T+0/T+1). State: `state/vn_theses/` + `state/vn_journal/`. | `register`, `list`, `transition`, `attach-position`, `close`, `review-due`, `mark-reviewed`, `postmortem`, `summary` | 27 |
| **`vn-canslim-screener`** | Sàng lọc CANSLIM (Mark Minervini) hiệu chỉnh cho VN. 5 trụ cột: C/A (EPS YoY), N (cách đỉnh 52w ≤5%), S (thanh khoản), L (RS / dẫn dắt ngành), I (room ngoại proxy cho dòng tiền tổ chức). Lọc trạng thái Kiểm soát/Hạn chế/Tạm ngừng. Grade A/B/C. | 1 binary CLI | 15 |
| **`vn-earnings-analyzer`** | Đánh giá phản ứng sau BCTC trên 5 yếu tố: gap, volume, trend 20D trước báo cáo, vị trí MA50/200, EPS surprise. Calibrate theo biên độ ±7% VN. Grade A→F. | 1 binary CLI | 15 |
| **`vn-pead-screener`** | Sàng lọc PEAD (post-earnings drift). Mode A scan độc lập; Mode B nhận output từ `vn-earnings-analyzer`. Tính chính xác trần/sàn VN (±7%/±10%/±15%), cảnh báo khi stop ≤ sàn. Target R-multiple. | 1 binary CLI | 15 |
| **`vn-margin-rules-monitor`** | Theo dõi danh sách margin per-CTCK + tier + Q-rated flag. `record` nạp CSV, `check` tra cứu (+`--warn-q-rated`), `report` thống kê, `history` thay đổi. State: `state/vn_margin/<broker>_margin_list.csv`. | `record`, `check`, `report`, `history` | 13 |
| **`vn-etf-screener`** | Chấm điểm ETF VN (VFMVN30, FUEVFVND, E1VFVN30, …) theo tracking error, premium/discount, expense ratio, volume 20D. Grade A→F. Hữu ích cho Core portfolio. | 1 binary CLI | 12 |
| **`vn-daily-brief`** | Orchestrator báo cáo buổi sáng — gọi `vn-sector-analyst`, `vn-foreign-room-tracker`, `vn-portfolio-manager` và ghi báo cáo tổng hợp `reports/vn_daily_brief_<date>.md`. Cờ `--strict` để fail-fast khi sub-skill lỗi. | 1 binary CLI | 8 |
| **Tổng** | **21 skills shipped** | | **~400 tests pass** |

---

## Cài đặt nhanh

### 1. Clone repo

```bash
git clone https://github.com/<your-fork>/xone-trading-skills.git
cd xone-trading-skills
```

### 2. Cài Python dependencies

```bash
# Dev deps (pytest, ruff, v.v.)
pip install -e ".[dev]"

# VN data layer (vnstock) — chỉ cần cho skills fetch data
pip install -e ".[vn]"
```

### 3. Chạy thử skill đầu tiên

```bash
# Test vn-position-sizer (không cần API key, không cần Internet)
python skills/vn-position-sizer/scripts/vn_position_sizer.py \
  --account-size 1000000000 \
  --symbol VIC --exchange hose \
  --entry 45000 --stop 42000 --risk-pct 1.0 \
  --output-dir reports/

# Output: số CP nên mua, phí + thuế dự kiến, T+2.5 calendar, cảnh báo nếu stop dưới sàn
```

### 4. Dùng với Claude Code

```bash
# Copy skill folder vào Claude Code skills directory
# Mặc định: ~/.claude/skills/ (macOS/Linux), %USERPROFILE%\.claude\skills\ (Windows)

# Trong Claude Code, hỏi:
# "Tính giúp tôi mua bao nhiêu cổ phiếu VIC với account 1 tỷ, entry 45000, stop 42000"
# → Claude sẽ trigger vn-position-sizer skill
```

### 5. Dùng với Claude Web App

Tất cả 21 kỹ năng `vn-*` đã được đóng gói thành các tệp `.skill` ZIP tại thư mục `skill-packages/`. Để sử dụng:
1. Đăng nhập vào [Claude Web App](https://claude.ai)
2. Kéo thả tệp `.skill` (ví dụ: `skill-packages/vn-canslim-screener.skill`) vào cửa sổ chat.
3. Yêu cầu Claude thực thi kỹ năng!


---

## Workflow ngày điển hình (end-to-end)

Một ngày làm việc của swing trader VN có thể như sau:

```
┌──────────────────────────────────────────────────────────────────────┐
│  SÁNG (trước phiên 9:00)                                             │
│                                                                      │
│  1. vn-data-fetcher ohlcv --symbols VCB,BID,VIC,HPG,FPT,VNM,...     │
│     → reports/vn_ohlcv_*.json                                        │
│                                                                      │
│  2. vn-sector-analyst --ohlcv-glob 'reports/vn_ohlcv_*.json'        │
│     → reports/vn_sector_analysis_*.json                              │
│     → Ngành nào dẫn dắt? Banking strong? Real Estate yếu?           │
│                                                                      │
│  3. vn-foreign-room-tracker record --input today_room.csv           │
│     (nhập room từ bảng giá CTCK)                                    │
│     vn-foreign-room-tracker report                                   │
│     → reports/vn_foreign_room_report_*.json                          │
│     → Mã nào vừa giải phóng room? Mã nào đầy?                       │
└──────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────┐
│  TRONG PHIÊN (9:00-15:00)                                            │
│                                                                      │
│  4. Identify breakout candidate trong ngành dẫn dắt + room hot       │
│     (manual hoặc chờ vn-vcp-screener sắp tới)                       │
│                                                                      │
│  5. vn-breakout-trade-planner \                                     │
│       --symbol FPT --pivot 142000 --stop 135000 --risk-pct 1.0 \    │
│       --sector-analysis-file reports/vn_sector_*.json \             │
│       --foreign-room-file reports/vn_foreign_room_*.json            │
│     → Full trade plan với guardrails VN, T+2.5 calendar              │
│                                                                      │
│  6. Đặt lệnh ở CTCK theo trade plan                                 │
└──────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────┐
│  CHIỀU (sau phiên đóng)                                              │
│                                                                      │
│  7. vn-portfolio-manager add --symbol FPT --shares 700 ...          │
│     (ghi lệnh đã khớp)                                              │
│                                                                      │
│  8. vn-portfolio-manager summary --prices "FPT:142500,..." \        │
│       --account-size 1000000000 \                                    │
│       --max-position-pct 10 --max-sector-pct 30                      │
│     → NAV, P&L unrealized, cảnh báo concentration                   │
└──────────────────────────────────────────────────────────────────────┘
```

Xem ví dụ runnable đầy đủ trong [`examples/vn-daily-swing/`](examples/vn-daily-swing/).

---

## Triết lý Core + Satellite

Project theo cấu trúc **Core + Satellite** dành cho nhà đầu tư cá nhân có quỹ thời gian hạn chế:

| Lớp | Mục tiêu | Skills VN liên quan |
| --- | --- | --- |
| **Core** | Đầu tư dài hạn, cổ tức, ETF, portfolio management | `vn-portfolio-manager`, `vn-dividend-screener` (sắp) |
| **Satellite** | Swing trading, breakout, momentum 1-8 tuần | `vn-breakout-trade-planner`, `vn-vcp-screener` (sắp), `vn-pullback-screener` (sắp) |
| **Advanced Satellite** | Phái sinh VN30 Futures, event-driven | `vn30-derivatives-planner` (sắp) |
| **Lớp dùng chung** | Market regime, risk management, position sizing, journaling | `vn-position-sizer`, `vn-sector-analyst`, `vn-foreign-room-tracker`, `vn-market-mechanics` |

**Quy tắc vàng:** Không trộn timeframe Core và Satellite trong cùng một lệnh. Mỗi quyết định phải biết rõ nó thuộc nhóm nào.

---

## Cấu trúc project

```
xone-trading-skills/
├── skills/
│   ├── vn-market-mechanics/      ← Tham chiếu chuẩn TTCK VN
│   ├── vn-position-sizer/         ← Sizing với lô 100, fees, T+2.5
│   ├── vn-data-fetcher/           ← Wrapper vnstock + cache
│   ├── vn-portfolio-manager/      ← Portfolio VND sau-phí-thuế
│   ├── vn-foreign-room-tracker/   ← Room ngoại daily monitor
│   ├── vn-sector-analyst/         ← Rotation 11 ngành VN-Index
│   ├── vn-breakout-trade-planner/ ← Integrative trade plan
│   ├── position-sizer/, kanchi-*, vcp-screener/, ...
│   │                              ← ~54 skill quốc tế (US) giữ cho advanced
│   └── (chi tiết: skill-catalog)
├── examples/
│   └── vn-daily-swing/            ← Ví dụ end-to-end VN
├── state/                          ← Local runtime state
│   ├── vn_portfolio/               ← holdings.csv, closed.csv
│   ├── vn_foreign_room/            ← history.csv
│   └── vn_market_data/             ← OHLCV cache
├── skill-packages/                 ← .skill ZIP cho Claude web app
├── scripts/                        ← Doc generator, pipelines
├── docs/                           ← Jekyll site (English)
└── PROJECT_VISION.md               ← Tầm nhìn project (v0.2 — VN-first)
```

---

## Nguồn dữ liệu

Mặc định dùng thư viện open source **[`vnstock`](https://github.com/thinh-vu/vnstock)** — wrapper tổng hợp API miễn phí của TCBS, SSI, VCI, VND.

```bash
pip install vnstock
# Hoặc qua optional dep của project:
pip install -e ".[vn]"
```

Chi tiết về vnstock, fallback sources, và quy ước data: xem [`skills/vn-market-mechanics/references/vn_data_sources.md`](skills/vn-market-mechanics/references/vn_data_sources.md).

---

## Khi nào KHÔNG nên dùng repo này

- Bạn muốn **trading bot tự động** — repo này không tự đặt lệnh.
- Bạn muốn **tín hiệu mua/bán** — repo cung cấp framework + analysis, không phải signal service.
- Bạn muốn **scalping intraday** — T+2.5 settlement không cho phép. Repo phù hợp với swing (1-8 tuần).
- Bạn không muốn **ghi journal / review** — process chính của repo là Plan → Trade → Record → Review.

---

## Đóng góp

Project dưới **MIT License**. Issues và PRs được chào đón. Các đóng góp hữu ích:

- Tinh chỉnh workflow recipes cho thị trường VN
- Cập nhật quy tắc thuế/phí khi UBCKNN thay đổi
- Test cases và fixture data cho `vn-*`
- Báo cáo lỗi tích hợp với `vnstock`
- Skill mới cho VN30 derivatives, ETF (E1VFVN30, FUEVFVND), v.v.

**Không xử lý:** yêu cầu tín hiệu mua/bán cụ thể, tư vấn cá nhân, lời hứa lợi nhuận.

---

## Liên kết

- Tầm nhìn project: [`PROJECT_VISION.md`](PROJECT_VISION.md)
- Trang docs (English): <https://xonevn-ai.github.io/xone-trading-skills/>
- Bản tiếng Anh README: [`README.md`](README.md)

---

**Mantra:** Empower solo traders, growing together — **Trao quyền cho trader cá nhân, cùng nhau phát triển.**
