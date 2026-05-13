# VN Daily Brief — Quy trình Morning Routine

## Mục tiêu

Trước phiên 9:00 sáng, trader cần một bức tranh tổng thể nhanh về:
1. **Rotation ngành** — ngành nào dẫn dắt / yếu dần
2. **Dòng tiền nước ngoài** — mã nào vừa giải phóng room, đầy room, spike up/down
3. **Trạng thái danh mục** — vị thế hiện hữu, sector concentration, lãi/lỗ chưa thực hiện

Skill `vn-daily-brief` orchestrate các sub-skill sau và xuất một báo cáo duy nhất:

| Bước | Sub-skill | Đầu vào | Đầu ra |
| --- | --- | --- | --- |
| 1 | `vn-sector-analyst` | `reports/vn_ohlcv_*.json` | rotation ngành 5D/20D/60D + regime hint |
| 2 | `vn-foreign-room-tracker report` | `state/vn_foreign_room/` history.csv | room delta + alerts |
| 3 | `vn-portfolio-manager summary` | `state/vn_portfolio/` + giá hiện tại | net P&L, sector breakdown |

Báo cáo tổng hợp ghi tại `reports/vn_daily_brief_<YYYY-MM-DD>.md`.

## Khi nào dùng

- Sáng sớm (trước 9:00) sau khi đã chạy `vn-data-fetcher ohlcv` cho universe và `vn-foreign-room-tracker record` để cập nhật snapshot room mới nhất.
- Trước khi quyết định mở vị thế mới hoặc thoát vị thế cũ — daily brief cho biết bối cảnh.

## Khi nào KHÔNG dùng

- Khi sub-skill phụ thuộc bị lỗi mà bạn muốn hard-fail thay vì best-effort — dùng `--strict` để exit non-zero.
- Khi cần phân tích chuyên sâu một mã — `vn-daily-brief` chỉ là overview, không thay thế cho `vn-sector-analyst`, `vn-foreign-room-tracker history`, `vn-vcp-screener`, v.v.

## Tham chiếu vn-market-mechanics

Báo cáo daily brief dùng:
- [`vn_trading_rules.md`](../../vn-market-mechanics/references/vn_trading_rules.md) — T+2.5 settlement, giờ phiên, status flags
- [`vn_foreign_ownership.md`](../../vn-market-mechanics/references/vn_foreign_ownership.md) — định nghĩa room ngoại
- [`vn_fees_and_taxes.md`](../../vn-market-mechanics/references/vn_fees_and_taxes.md) — accounting cho portfolio summary

## Flags

| Flag | Mặc định | Mô tả |
| --- | --- | --- |
| `--ohlcv-glob` | `reports/vn_ohlcv_*.json` | Glob của OHLCV JSON cho vn-sector-analyst |
| `--room-state-dir` | `state/vn_foreign_room` | Thư mục state của vn-foreign-room-tracker |
| `--portfolio-state-dir` | `state/vn_portfolio` | Thư mục state của vn-portfolio-manager |
| `--prices` | (rỗng) | Giá hiện tại CSV `SYM:PRICE` cho portfolio mark-to-market |
| `--account-size` | `1000000000` | Quy mô tài khoản VND |
| `--output-dir` | `reports/` | Thư mục báo cáo tổng hợp |
| `--strict` | (off) | Exit non-zero khi bất kỳ sub-skill nào lỗi |
| `--lookback-days` | `1` | Lookback so sánh foreign-room (1 = hôm qua) |

## Cảnh báo

- **Sub-skill brittle**: vn-daily-brief gọi các sub-skill qua `subprocess.run`. Nếu một sub-skill thay đổi CLI signature, daily-brief sẽ lỗi. Phòng tránh bằng pinned `pyproject.toml` version + integration tests.
- **Không cache**: Mỗi lần chạy gọi mới các sub-skill. Tốc độ phụ thuộc vào sub-skill chậm nhất (thường là `vn-portfolio-manager summary` khi có nhiều vị thế).
