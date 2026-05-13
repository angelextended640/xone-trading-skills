---
name: vn-margin-rules-monitor
description: Theo dõi danh sách margin per-CTCK (TCBS, SSI, VND, HCM, VCI, ...) tại Việt Nam, kèm cờ Q-rated (Kiểm soát/Hạn chế/Tạm ngừng/Cảnh báo). Subcommands record/check/report/history. Trigger khi user hỏi "FPT có được margin ở TCBS không", "cổ phiếu nào bị cắt margin", "VIC bị Q-rated chưa". Vietnam stock margin eligibility & Q-rated flag monitoring across multiple brokers.
---

# Theo dõi Quy định Ký quỹ (Margin Rules Monitor — VN)

## Tổng quan

Skill này theo dõi danh sách cổ phiếu được phép giao dịch ký quỹ (margin) tại các Công ty Chứng khoán Việt Nam, cập nhật theo snapshot quarterly hoặc khi có thông báo mới của CTCK.

Cờ Q-rated (Kiểm soát / Hạn chế / Tạm ngừng / Cảnh báo) là nguyên nhân chính bị **cắt margin đột ngột** + nguy cơ **call chéo** trong portfolio.

## Khi nào dùng

- **Trước khi đặt lệnh margin**: `check --symbol FPT --warn-q-rated`
- **Quarterly review**: `report` để xem distribution margin của universe
- **Khi CTCK ra thông báo cắt margin**: `record` để update snapshot
- **Audit trail**: `history` để xem thay đổi danh sách qua thời gian

**KHÔNG dùng để:**

- Dự báo cắt margin trong tương lai (skill chỉ track, không predict)
- Tra cứu tỷ lệ margin real-time (skill dùng snapshot, không gọi API broker)

## Workflow

### Bước 1 — Cập nhật snapshot từ CTCK

CSV input format:
```csv
symbol,rate,note
FPT,50,
VIC,30,Q-rated
HPG,40,
VHM,0,Suspended margin
```

```bash
python skills/vn-margin-rules-monitor/scripts/vn_margin_monitor.py record \
  --broker TCBS \
  --csv data/tcbs_margin_2026-05-13.csv
```

Snapshot ghi vào `state/vn_margin/tcbs_margin_list.csv` (latest) và `state/vn_margin/history/tcbs_2026-05-13.csv` (history).

### Bước 2 — Tra cứu trước khi giao dịch

```bash
# Basic check across all brokers
python skills/vn-margin-rules-monitor/scripts/vn_margin_monitor.py check --symbol FPT

# Với cảnh báo Q-rated (exit non-zero qua stderr nếu hit)
python skills/vn-margin-rules-monitor/scripts/vn_margin_monitor.py check --symbol VIC --warn-q-rated
```

Output: rate margin của symbol tại mỗi CTCK đã record, + warning nếu note chứa Q-rated.

### Bước 3 — Báo cáo tổng hợp

```bash
python skills/vn-margin-rules-monitor/scripts/vn_margin_monitor.py report --output-dir reports/
```

Báo cáo tại `reports/vn_margin_report_<timestamp>.json` — gồm:
- Tổng số mã margin/CTCK
- Tỷ lệ trung bình
- Số mã rate=0 (không cho vay)
- Số mã Q-rated + list

### Bước 4 — Lịch sử snapshot

```bash
python skills/vn-margin-rules-monitor/scripts/vn_margin_monitor.py history --broker TCBS
```

Liệt kê tất cả snapshot dates + row count cho CTCK đó. Diff giữa các date cho biết: ai bị thêm vào / bỏ ra danh sách margin.

## Output

`reports/vn_margin_<command>_<timestamp>.json`:

```json
{
  "schema_version": "1.0",
  "as_of": "2026-05-13T08:30:00+07:00",
  "brokers": [
    {
      "broker": "TCBS",
      "total_symbols": 250,
      "avg_rate_pct": 42.5,
      "zero_rate_count": 8,
      "q_rated_count": 5,
      "q_rated_symbols": ["VIC", "HSG", "POW", "SBT", "FLC"]
    }
  ]
}
```

## Tham chiếu vn-market-mechanics

- [`vn_trading_rules.md`](../vn-market-mechanics/references/vn_trading_rules.md) — UBCKNN baseline rules, T+2.5 settlement (margin position cũng tuân thủ T+2.5)
- [`vn_price_limits_orders.md`](../vn-market-mechanics/references/vn_price_limits_orders.md) — biên độ giá driving force-sell mechanic
- [`vn_fees_and_taxes.md`](../vn-market-mechanics/references/vn_fees_and_taxes.md) — broker fee context

Chi tiết Q-rated semantics + risk: [`references/vn_margin_rules.md`](references/vn_margin_rules.md).
