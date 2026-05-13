---
name: vn-foreign-room-tracker
description: Theo dõi room ngoại (foreign ownership room) cho watchlist cổ phiếu HOSE/HNX. Lưu snapshot hàng ngày, phát hiện room đầy / room giải phóng, alert thay đổi đột biến. State CSV dưới state/vn_foreign_room/. Kích hoạt khi user muốn theo dõi sở hữu khối ngoại, kiểm tra room còn lại cho mã, hoặc nhận alert về thay đổi room. Vietnam foreign ownership room tracker for HOSE/HNX watchlists — daily snapshots, full-room/release detection, change alerts. Local CSV state.
---

# VN Foreign Room Tracker — Theo dõi room ngoại

## Tổng quan

Theo dõi **room ngoại** (foreign ownership room) — tỷ lệ tối đa nhà đầu tư nước ngoài được sở hữu — cho danh sách cổ phiếu được quan tâm.

Room ngoại là **khái niệm chỉ có ở thị trường VN** (không có ở Mỹ). Một số mã thường xuyên **room đầy** (FPT, MWG, VNM, ngân hàng) — đây là tín hiệu nhu cầu khối ngoại cao. Khi room **giải phóng** (nước ngoài bán ra) hoặc **đột nhiên đầy** (nước ngoài mua mạnh), thường đi kèm biến động giá.

Skill này:
- Ingest dữ liệu room hàng ngày từ CSV/JSON (manual hoặc từ source khác)
- Lưu snapshot rolling dưới `state/vn_foreign_room/history.csv`
- Tạo báo cáo: room hiện tại, delta vs N ngày trước, alert (full / release / spike)

**Không** tự động fetch room — vnstock không có endpoint thống nhất; phải nhập từ bảng giá CTCK hoặc HSX. Hỗ trợ data source thay thế xem `skills/vn-market-mechanics/references/vn_foreign_ownership.md`.

## Khi nào dùng

- User có watchlist mã và muốn check room ngoại còn lại hôm nay
- Cần phát hiện cổ phiếu **vừa giải phóng room** (cơ hội mua khi room mở lại)
- Cần phát hiện cổ phiếu **room đột nhiên đầy** (tín hiệu cầu mạnh)
- Bổ trợ cho `vn-sector-analyst`, `vn-vcp-screener` (lọc thêm theo dòng vốn ngoại)

## Điều kiện tiên quyết

- Python 3.9+ (chỉ standard library)
- Không cần vnstock cho V1 — input là CSV thủ công hoặc fixture
- Tham chiếu: `skills/vn-market-mechanics/references/vn_foreign_ownership.md`

## Workflow

### Subcommands

| Subcommand | Mục đích |
| --- | --- |
| `record` | Ingest CSV/JSON snapshot vào history.csv |
| `report` | Báo cáo room hiện tại + delta + alerts |
| `history` | Xem chuỗi thời gian của 1 mã |

### Lệnh mẫu

```bash
# 1. Tạo CSV input (manual nhập từ bảng giá CTCK)
cat > /tmp/today_room.csv <<EOF
symbol,room_total,room_used,room_remaining
VIC,1869983116,1812345678,57637438
FPT,981234567,981234567,0
HPG,2456789012,1456789012,1000000000
MWG,584567890,584000000,567890
EOF

# 2. Record snapshot vào state
python3 skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py record \
  --input /tmp/today_room.csv \
  --as-of 2026-05-13 \
  --state-dir state/vn_foreign_room/

# 3. Báo cáo với alert
python3 skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py report \
  --state-dir state/vn_foreign_room/ \
  --output-dir reports/ \
  --full-threshold 99 --release-threshold 90 \
  --lookback-days 5

# 4. Xem history 1 mã
python3 skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py history \
  --symbol VIC --days 30 \
  --state-dir state/vn_foreign_room/
```

## State format

`state/vn_foreign_room/history.csv`:

```csv
as_of_date,symbol,room_total,room_used,room_remaining,room_used_pct
2026-05-12,VIC,1869983116,1810000000,59983116,96.79
2026-05-13,VIC,1869983116,1812345678,57637438,96.92
2026-05-12,FPT,981234567,981234567,0,100.00
2026-05-13,FPT,981234567,981000000,234567,99.98
```

## Output format

### Report

```json
{
  "schema_version": "1.0",
  "subcommand": "report",
  "as_of": "2026-05-13T08:00:00+07:00",
  "latest_date": "2026-05-13",
  "comparison_date": "2026-05-08",
  "rows": [
    {
      "symbol": "VIC",
      "room_used_pct": 96.92,
      "room_remaining": 57637438,
      "change_pct": 0.13,
      "change_remaining": -2345678,
      "status": "high_usage"
    },
    {
      "symbol": "FPT",
      "room_used_pct": 99.98,
      "room_remaining": 234567,
      "change_pct": -0.02,
      "change_remaining": 234567,
      "status": "released"
    }
  ],
  "alerts": [
    {"symbol": "FPT", "type": "released", "msg": "FPT vừa giải phóng room (99.98% trong ngưỡng release)"},
    {"symbol": "VIC", "type": "high_usage", "msg": "VIC room used 96.92%, gần đầy"}
  ]
}
```

### Status values

| Status | Ý nghĩa |
| --- | --- |
| `full` | room_used_pct ≥ full_threshold (mặc định 99%) |
| `high_usage` | release_threshold ≤ room_used_pct < full_threshold |
| `normal` | < release_threshold |
| `released` | Vừa giải phóng room (đã full → giảm dưới full_threshold trong lookback) |
| `spike_up` | room_used_pct tăng > 5% trong lookback |
| `spike_down` | room_used_pct giảm > 5% trong lookback |

## Nguyên tắc

1. **Append-only history** — Mỗi `record` thêm rows mới, không sửa cũ. Cho phép phân tích trend đầy đủ.
2. **Manual data acceptable** — V1 chấp nhận user nhập số liệu thủ công; tự động hoá sẽ làm sau khi có data source ổn định.
3. **Alert hữu ích, không spam** — Chỉ alert khi có thay đổi đáng kể (vượt threshold) hoặc trạng thái mới (released/spike).
4. **Pair với screener** — Kết quả room có thể join với output `vn-vcp-screener` hoặc `vn-sector-analyst` để ưu tiên mã có dòng vốn ngoại tốt.

## Nguồn data thay thế

Tham khảo `skills/vn-market-mechanics/references/vn_foreign_ownership.md`:
- HOSE: https://www.hsx.vn/Modules/Listed/Web/SymbolView (mục Tỷ lệ sở hữu nước ngoài)
- Bảng giá CTCK (SSI iBoard, VPS, VNDirect): 3 cột "Room ngoại còn lại / Đã sở hữu / Tổng room"
- FireAnt, CafeF API: có endpoint trả về room theo ngày

Trong tương lai (V2): tích hợp với vnstock khi API foreign-room ổn định.
