---
name: vn-canslim-screener
description: Sàng lọc cổ phiếu Việt Nam theo phương pháp CANSLIM của William O'Neil, tinh chỉnh cho HOSE/HNX/UPCOM. 5 trụ cột — EPS YoY (C/A), giá gần đỉnh 52w (N), volume 20D (S), RS rating (L), dòng tiền khối ngoại 10D làm proxy cho I. Mặc định loại cổ phiếu Kiểm soát/Hạn chế/Tạm ngừng. Grade A/B/C. Trigger khi user hỏi "CANSLIM Việt Nam", "cổ phiếu tăng trưởng mạnh nhất VN", "lọc CANSLIM cho HOSE". Vietnam CANSLIM screener (Minervini/O'Neil) adapted for VN price bands, lot 100, and foreign-flow proxy for institutional sponsorship.
---

# VN CANSLIM Screener — Sàng lọc CANSLIM cho cổ phiếu Việt Nam

## Tổng quan

Phương pháp CANSLIM của William O'Neil chấm điểm cổ phiếu theo 7 trụ cột growth. Skill này tinh chỉnh cho VN:

| Trụ cột | Nghĩa | Ngưỡng VN |
| --- | --- | --- |
| **C & A** | Current + Annual Earnings | `eps_growth_yoy_pct ≥ 20.0` |
| **N** | New 52-Week High | `price ≥ high_52w × 0.95` (cách đỉnh ≤ 5%) |
| **S** | Supply & Demand (Volume) | `volume_20d_avg ≥ 100,000 CP` |
| **L** | Leader (Relative Strength) | `rs_rating ≥ 80` |
| **I** | Institutional Sponsorship (proxy) | `foreign_net_buy_10d_vnd ≥ 0` |
| **M** | Market Direction | `vn-sector-analyst regime ≠ risk-off` (advisory) |

Output là Grade A/B/C — Grade A = đủ 5/5 trụ cột; Grade B = 4/5.

Tham chiếu phương pháp luận chi tiết + tại sao lại tinh chỉnh: [`references/vn_canslim_methodology.md`](references/vn_canslim_methodology.md).

## Khi nào dùng

- Tìm cổ phiếu growth momentum cho swing 4-12 tuần
- Kết hợp với `vn-sector-analyst` (chọn ngành dẫn dắt) + `vn-foreign-room-tracker` (room hot) → high-quality setup
- Sau khi `vn-data-fetcher fundamentals` cho universe để có `eps_growth_yoy_pct`

**KHÔNG dùng khi:**

- Thị trường downtrend rõ (`vn-sector-analyst regime == risk-off`) — M-pillar fail
- Universe < 30 mã — sample size nhỏ → grade A không có nghĩa
- Cổ phiếu đang Q-rated / Kiểm soát (skill mặc định loại; check `vn-margin-rules-monitor` trước)

## Workflow

### Bước 1 — Build universe JSON

Universe schema (xem `references/sample_universe.json` cho ví dụ đầy đủ):

```json
[
  {
    "symbol": "FPT",
    "price": 135000,
    "high_52w": 136000,
    "volume_20d_avg": 2500000,
    "eps_growth_yoy_pct": 22.5,
    "rs_rating": 85,
    "foreign_net_buy_10d_vnd": 50000000000,
    "sector": "Công nghệ thông tin",
    "status": "Normal"
  }
]
```

Cách build universe từ live data:

```bash
# 1. OHLCV cho universe
python skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols FPT,VIC,VHM,HPG,VNM,VCB,BID,CTG,MWG,SSI \
  --start 2025-05-13 --end 2026-05-13

# 2. Fundamentals (EPS growth YoY)
python skills/vn-data-fetcher/scripts/vn_data_fetcher.py fundamentals \
  --symbols FPT,VIC,VHM,HPG,VNM,VCB,BID,CTG,MWG,SSI --period quarter

# 3. Foreign flow snapshot
python skills/vn-data-fetcher/scripts/vn_data_fetcher.py foreign-flow \
  --symbols FPT,VIC,VHM,HPG,VNM,VCB,BID,CTG,MWG,SSI

# 4. Tổng hợp manually (hoặc dùng Claude) thành universe.json
```

### Bước 2 — Chạy screener

```bash
# Default — grade C+ và bỏ qua flagged
python skills/vn-canslim-screener/scripts/vn_canslim_screener.py \
  --universe my_universe.json \
  --output-dir reports/

# Chỉ grade A/B với M-pillar check
python skills/vn-canslim-screener/scripts/vn_canslim_screener.py \
  --universe my_universe.json \
  --min-grade B \
  --market-regime risk-on \
  --output-dir reports/

# Bao gồm cả flagged (research mode, không trade thật)
python skills/vn-canslim-screener/scripts/vn_canslim_screener.py \
  --universe my_universe.json --include-flagged
```

### Bước 3 — Action với output

Báo cáo tại `reports/vn_canslim_screener_<timestamp>.{json,md}`.

- Grade A → Đưa vào watchlist + đăng ký thesis qua `vn-trader-memory thesis_ingest`
- Grade B → Monitor 1 trụ cột yếu (thường là I — foreign flow); chờ thêm
- Grade C → Bỏ qua

## Output

JSON top-level:

```json
{
  "schema_version": "1.0",
  "as_of": "2026-05-13T08:30:00+07:00",
  "universe_size": 50,
  "results_count": 8,
  "skipped_count": 3,
  "min_grade": "C",
  "market_regime": "risk-on",
  "market_advisory": null,
  "results": [ ... ],
  "skipped": [ { "symbol": "HSG", "reason": "status=Kiểm soát" } ]
}
```

Markdown report là bảng `Symbol / Sector / Grade / Score / Price / Δ 52w / EPS YoY / RS / NN10D` với VND formatted (thousands separator).

## Tham chiếu vn-market-mechanics

- [`vn_trading_rules.md`](../vn-market-mechanics/references/vn_trading_rules.md) — status flags driving SKIP_STATUSES default
- [`vn_price_limits_orders.md`](../vn-market-mechanics/references/vn_price_limits_orders.md) — biên độ giá định nghĩa N pillar
- [`vn_foreign_ownership.md`](../vn-market-mechanics/references/vn_foreign_ownership.md) — foreign flow proxy cho I pillar
- [`vn_data_sources.md`](../vn-market-mechanics/references/vn_data_sources.md) — vnstock fundamentals + foreign-flow endpoints
