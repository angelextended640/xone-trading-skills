---
name: vn-trader-memory
description: Quản lý vòng đời thesis giao dịch cho cổ phiếu Việt Nam — Plan → Trade → Record → Review → Improve. Đăng ký từ vn-*screener output, lifecycle IDEA → ENTRY_READY → ACTIVE → CLOSED, attach position size, generate postmortem với MAE/MFE từ vnstock. VND-aware, lot 100, fee + tax trong realized P&L. Kích hoạt khi user hỏi "ghi thesis", "lifecycle trade", "review nào tới hạn", "postmortem mã VIC", "trade memory". Vietnam trader memory — thesis lifecycle + postmortem for VN equity trades, vnstock-backed (no FMP dependency), VND + lot-100 + fee/tax aware.
---

# VN Trader Memory — Vòng lặp học hỏi cho VN trader

## Tổng quan

Skill này đóng vòng lặp **Plan → Trade → Record → Review → Improve** cho swing trader VN. Bản chuyển thể từ `trader-memory-core` (skill quốc tế dùng FMP) với các thay đổi quan trọng cho thị trường VN:

- **VNStock thay FMP** — postmortem MAE/MFE fetch giá qua vnstock
- **VND currency** — mọi field `position_value`, `pnl` đều là VND (không phải USD)
- **Lot validation** — `position.shares` phải là bội số 100 (quy tắc HOSE/HNX/UPCOM)
- **T+2.5 aware** — `review_interval_days` mặc định 5 (so với 30 quốc tế); MAE/MFE skip T+0/T+1
- **Fee + tax trong realized P&L** — `outcome.broker_fee_vnd` + `outcome.sale_tax_vnd` được tính riêng, net P&L = gross − fees − tax
- **State dir riêng** — `state/vn_theses/` + `state/vn_journal/` (không đụng `state/theses/` của bản international)
- **Adapter registry VN** — nhận output từ `vn-vcp-screener`, `vn-pullback-screener`, `vn-dividend-screener`, `vn-breakout-trade-planner`

## Khi nào dùng

- Đăng ký thesis mới sau khi sàng lọc (vn-vcp / vn-pullback / vn-dividend)
- Theo dõi vị thế đang mở: review hàng tuần / fortnight
- Đóng vị thế và tự động generate journal entry
- Học từ thua/thắng quá khứ thông qua summary / postmortem
- Pair với `vn-portfolio-manager` (đầu vào realized exit) và `vn-position-sizer` (attach position)

**KHÔNG** dùng cho:
- Tracking real-time giá intraday — đây là long-term memory
- Trading bot tự động — đây là decision-support journal

## Điều kiện tiên quyết

- Python 3.9+ với pyyaml + jsonschema
- `vnstock>=3.0` (nếu muốn auto-fetch MAE/MFE qua vnstock; có thể fallback manual)
- Tham chiếu: `references/vn_ingest_adapters.md`

## Workflow

### Subcommands

| Subcommand | Mục đích |
| --- | --- |
| `register` | Đăng ký thesis mới từ vn-*screener JSON output |
| `list` | Liệt kê theses theo filter (status, ticker, sector) |
| `get` | Xem chi tiết một thesis |
| `transition` | Chuyển status (IDEA → ENTRY_READY → ACTIVE → CLOSED) |
| `attach-position` | Gắn output từ vn-position-sizer vào thesis |
| `close` | Đóng vị thế với exit price + date; auto compute net P&L |
| `review-due` | Liệt kê theses tới hạn review |
| `mark-reviewed` | Đánh dấu thesis đã review (cập nhật next_review_date) |
| `postmortem` | Generate markdown journal entry với MAE/MFE từ vnstock |
| `summary` | Stats: win rate, avg P&L%, sector breakdown |

### Bước 1: Register thesis từ screener output

```bash
# Sau khi vn-vcp-screener output candidates
python3 skills/vn-trader-memory/scripts/vn_thesis_ingest.py \
  --source vn-vcp-screener \
  --input reports/vn_vcp_screener_2026-05-13_*.json \
  --ticker FPT \
  --state-dir state/vn_theses/
```

Tạo file `state/vn_theses/th_fpt_pvt_20260513_xxxx.yaml` với status IDEA.

### Bước 2: Attach position size

```bash
# Sau khi vn-position-sizer compute size
python3 skills/vn-trader-memory/scripts/vn_thesis_store.py attach-position \
  --thesis-id th_fpt_pvt_20260513_xxxx \
  --position-sizer-output reports/vn_position_sizer_*.json \
  --state-dir state/vn_theses/
```

### Bước 3: Transition lifecycle

```bash
# Sau khi đặt lệnh thành công
python3 skills/vn-trader-memory/scripts/vn_thesis_store.py transition \
  --thesis-id th_fpt_pvt_20260513_xxxx \
  --to ACTIVE \
  --actual-entry-price 142000 --actual-entry-date 2026-05-13 \
  --state-dir state/vn_theses/
```

### Bước 4: Review định kỳ

```bash
# Liệt kê theses tới hạn review (default 5 ngày sau entry)
python3 skills/vn-trader-memory/scripts/vn_thesis_review.py review-due \
  --as-of 2026-05-20 \
  --state-dir state/vn_theses/

# Đánh dấu đã review
python3 skills/vn-trader-memory/scripts/vn_thesis_review.py mark-reviewed \
  --thesis-id th_fpt_pvt_20260513_xxxx \
  --status OK \
  --note "FPT vẫn trên MA20, room ngoại 99.8%" \
  --state-dir state/vn_theses/
```

### Bước 5: Close + postmortem

```bash
# Đóng vị thế
python3 skills/vn-trader-memory/scripts/vn_thesis_store.py close \
  --thesis-id th_fpt_pvt_20260513_xxxx \
  --exit-price 152000 --exit-date 2026-06-04 \
  --exit-reason target_hit \
  --state-dir state/vn_theses/

# Generate postmortem với MAE/MFE
python3 skills/vn-trader-memory/scripts/vn_thesis_review.py postmortem \
  --thesis-id th_fpt_pvt_20260513_xxxx \
  --state-dir state/vn_theses/ \
  --journal-dir state/vn_journal/
```

## VN-specific accounting

`outcome` block trong thesis YAML:

```yaml
outcome:
  gross_pnl_vnd: 7000000      # (152000 - 142000) × 1000 shares
  broker_fee_vnd: 441000      # 0.15% × (entry_value + exit_value)
  sale_tax_vnd: 152000        # 0.1% × exit_value
  net_pnl_vnd: 6407000        # gross - fees - tax
  net_pnl_pct: 4.51           # vs entry_value
  holding_days: 22            # T+2.5 already excluded from MAE/MFE
  mae_pct: -1.8               # max adverse excursion (from T+3 onward)
  mfe_pct: 8.2                # max favourable excursion
  mae_mfe_source: "vnstock"   # or "manual" if vnstock unavailable
```

## Output Format

### Thesis YAML (state/vn_theses/<id>.yaml)

```yaml
thesis_id: th_fpt_pvt_20260513_a3f1
ticker: FPT
exchange: hose
thesis_type: pivot_breakout
created_at: 2026-05-13T10:00:00+07:00
updated_at: 2026-05-13T10:00:00+07:00
status: ACTIVE
status_history:
  - status: IDEA
    at: 2026-05-13T10:00:00+07:00
    reason: "Registered from vn-vcp-screener output"
  - status: ENTRY_READY
    at: 2026-05-13T10:30:00+07:00
    reason: "Position size confirmed"
  - status: ACTIVE
    at: 2026-05-13T14:30:00+07:00
    reason: "Lệnh khớp tại VPS"

entry:
  target_price: 142000
  stop_loss: 135000
  actual_price: 142000
  actual_date: 2026-05-13
  setup_type: vcp_breakout

position:
  shares: 700
  position_value_vnd: 99400000
  risk_vnd: 4900000
  risk_pct_of_account: 0.49
  account_size_vnd: 1000000000

monitoring:
  review_interval_days: 5
  next_review_date: 2026-05-18
  last_review_date: null
  review_status: null
  alerts: []

origin:
  skill: vn-vcp-screener
  output_file: reports/vn_vcp_screener_2026-05-13_*.json
  screening_grade: A
  screening_score: 88
  raw_provenance:
    contractions: 3
    base_total_range_pct: 18.2
    pivot_to_52w_high_pct: 3.5

market_context:
  sector: "Công nghệ"
  vn_index_at_entry: 1280.5

outcome: null  # populated after close
```

### Postmortem markdown (state/vn_journal/pm_<id>.md)

```markdown
# Postmortem — FPT VCP Breakout
**Thesis:** th_fpt_pvt_20260513_a3f1
**Holding:** 2026-05-13 → 2026-06-04 (22 trading days)
**Outcome:** WIN (+4.51% net)

## Original thesis
[from thesis YAML — screening grade, setup type, expected catalyst]

## Trade execution
- Entry: 142,000 VND × 700 shares = 99,400,000 VND
- Exit: 152,000 VND × 700 shares = 106,400,000 VND
- Gross P&L: +7,000,000 VND (+7.04%)
- Fees: 441,000 VND (broker 0.15% × 2)
- Sale tax: 152,000 VND (0.1%)
- **Net P&L: +6,407,000 VND (+6.45%)**

## Excursion analysis (T+3 onward)
- MAE: -1.8% (on 2026-05-19)
- MFE: +8.2% (on 2026-06-02, peak before exit)
- MAE/MFE source: vnstock daily closes

## Lessons
[fill manually]
```

## Resources

- `references/vn_ingest_adapters.md` — Per-screener adapter contracts
- `schemas/thesis.schema.json` — Full schema with VN-specific fields
- `scripts/vn_thesis_store.py` — CRUD
- `scripts/vn_thesis_ingest.py` — Adapter registry
- `scripts/vn_thesis_review.py` — Review + postmortem
- `scripts/vn_price_adapter.py` — vnstock-backed price fetch for MAE/MFE
- Cross-references:
  - `skills/vn-position-sizer/` — input to `attach-position`
  - `skills/vn-vcp-screener/`, `vn-pullback-screener/`, `vn-dividend-screener/`, `vn-breakout-trade-planner/` — input to `register`
  - `skills/vn-tax-fee-calculator/` — fee/tax constants reused

## Nguyên tắc

1. **YAML state, append-only history** — Thesis lifecycle changes accumulate; `status_history` never erased.
2. **Single source of truth per thesis** — Each `state/vn_theses/<id>.yaml` is canonical. Updates use tempfile + rename for atomicity.
3. **VN math throughout** — Fees + sale tax baked into close logic. No accidental USD/VND confusion.
4. **Lot-100 enforced** — Schema validation rejects positions where shares % 100 != 0.
5. **vnstock graceful fallback** — If MAE/MFE fetch fails, postmortem still generates with `mae_mfe_source: "manual"`.
6. **Review windows aware of T+2.5** — Default `review_interval_days = 5` aligns with "first sellable day + 2-3 sessions to assess".
