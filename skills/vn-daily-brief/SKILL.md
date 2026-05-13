---
name: vn-daily-brief
description: Báo cáo tổng hợp đầu ngày (Morning Routine) cho thị trường chứng khoán Việt Nam. Chạy luân chuyển dòng tiền ngành, biến động room ngoại, và trạng thái danh mục trong một lệnh duy nhất, xuất báo cáo markdown tổng hợp. VN composite morning-routine skill — orchestrates sector rotation, foreign-room delta, and portfolio summary into one consolidated markdown report.
---

# Báo cáo Tổng hợp Đầu ngày (VN Daily Brief)

## Tổng quan

Đây là skill "điều phối" (orchestrator). Mỗi sáng trước phiên 9:00, trader có thể chạy một lệnh duy nhất để lấy:

1. **Rotation ngành VN-Index** (qua `vn-sector-analyst`)
2. **Biến động room ngoại** (qua `vn-foreign-room-tracker report`)
3. **Trạng thái danh mục** (qua `vn-portfolio-manager summary`)

Báo cáo tổng hợp được lưu tại `reports/vn_daily_brief_<YYYY-MM-DD>.md` để review nhanh + reference trong nhật ký.

## Khi nào dùng

- Sáng sớm, sau khi đã chạy `vn-data-fetcher ohlcv` (lấy OHLCV) và `vn-foreign-room-tracker record` (cập nhật snapshot room hôm nay)
- Trước khi quyết định mở/đóng vị thế — daily brief cho bối cảnh
- Kết hợp với `vn-news-analyst` để bổ sung tin tức (Claude tự gọi sau)

**KHÔNG dùng để:**

- Phân tích chuyên sâu một mã (overview only)
- Thay thế cho việc đọc bảng giá trực tiếp trong phiên

## Workflow

### Bước 1 — Chuẩn bị dữ liệu input

```bash
# Cập nhật OHLCV (vn-data-fetcher)
python skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VCB,BID,CTG,VIC,VHM,HPG,FPT,MWG,VNM,SSI,VCI,GAS \
  --start 2026-04-01 --end 2026-05-13 \
  --output-dir reports/

# Cập nhật snapshot room (manual, ví dụ từ bảng giá CTCK)
python skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py record \
  --input examples/today_room.csv \
  --state-dir state/vn_foreign_room/
```

### Bước 2 — Chạy daily brief

```bash
# Default (tolerant: best-effort, không fail nếu sub-skill nào lỗi)
python skills/vn-daily-brief/scripts/vn_daily_brief.py \
  --ohlcv-glob "reports/vn_ohlcv_*.json" \
  --room-state-dir "state/vn_foreign_room" \
  --portfolio-state-dir "state/vn_portfolio" \
  --prices "FPT:142000,VIC:45000" \
  --account-size 1000000000 \
  --output-dir reports/

# Strict mode (exit 1 nếu bất kỳ sub-skill nào lỗi)
python skills/vn-daily-brief/scripts/vn_daily_brief.py --strict ...
```

### Bước 3 — Đọc báo cáo + bổ sung tin tức

Mở `reports/vn_daily_brief_<date>.md`. Mỗi section có:
- ✅ nếu sub-skill thành công, ⚠️ nếu lỗi
- Output gốc của sub-skill (fenced code khi cần preserve formatting)

Sau đó, hỏi Claude bổ sung `vn-news-analyst` để map tin tức → mã hưởng lợi/chịu tác động.

## Output

`reports/vn_daily_brief_<YYYY-MM-DD>.md` — markdown 3 section + header (timezone Asia/Ho_Chi_Minh):

```
# VN Daily Brief — 2026-05-13

_Generated at 2026-05-13_07:30:00 (Asia/Ho_Chi_Minh, UTC+7)_

## ✅ 1. Rotation ngành (vn-sector-analyst)
…

## ✅ 2. Biến động Room ngoại (vn-foreign-room-tracker report)
…

## ✅ 3. Trạng thái Danh mục (vn-portfolio-manager summary)
…
```

## Tham chiếu vn-market-mechanics

- [`vn_trading_rules.md`](../vn-market-mechanics/references/vn_trading_rules.md) — sessions, T+2.5, status flags
- [`vn_foreign_ownership.md`](../vn-market-mechanics/references/vn_foreign_ownership.md) — room concept
- [`vn_fees_and_taxes.md`](../vn-market-mechanics/references/vn_fees_and_taxes.md) — portfolio P&L accounting

Chi tiết workflow + cảnh báo: [`references/vn_daily_brief_workflow.md`](references/vn_daily_brief_workflow.md).
