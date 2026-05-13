---
name: vn-portfolio-manager
description: Quản lý danh mục cổ phiếu Việt Nam (VND) — thêm/bớt vị thế, theo dõi P&L sau phí 0.15% và thuế bán 0.1%, phân bổ theo ngành, exposure tổng. Lưu state local dưới state/vn_portfolio/. Kích hoạt khi user muốn theo dõi danh mục, kiểm tra phân bổ ngành, hoặc tính lợi nhuận sau phí thuế cho cổ phiếu VN. Vietnam portfolio manager (VND) — add/remove positions, after-fee/after-tax P&L, sector breakdown, total exposure. Local CSV state under state/vn_portfolio/.
---

# VN Portfolio Manager — Quản lý danh mục cổ phiếu Việt Nam

## Tổng quan

Quản lý danh mục cổ phiếu **HOSE/HNX/UPCOM** với:

- Lưu trữ vị thế mở dưới `state/vn_portfolio/holdings.csv`
- Lịch sử giao dịch đã đóng dưới `state/vn_portfolio/closed.csv`
- Tính P&L **sau phí môi giới 0.15%** và **thuế bán 0.1%** (theo `skills/vn-market-mechanics/references/vn_fees_and_taxes.md`)
- Tóm tắt phân bổ theo ngành
- Cảnh báo khi vượt giới hạn concentration (mặc định 10%/mã, 30%/ngành)

**Không** kết nối broker — nhập thủ công sau mỗi giao dịch. Đây là quyết định kiến trúc: nhiều CTCK Việt Nam không có API mở cho cá nhân, và việc tách "ghi nhận giao dịch" khỏi "thực hiện giao dịch" tăng tính kỷ luật.

## Khi nào dùng

- User muốn xem danh mục hiện tại, NAV, phân bổ ngành
- Cần nhập một giao dịch mới (mua/bán)
- Cần check một cổ phiếu mới có vi phạm giới hạn portfolio không
- Cần báo cáo P&L tháng/quý sau phí và thuế

## Điều kiện tiên quyết

- Python 3.9+ với pandas (kèm trong `[vn]` extras)
- Không cần API key
- Tham chiếu: `skills/vn-market-mechanics/references/vn_fees_and_taxes.md`

## Workflow

### Subcommands

| Subcommand | Mục đích |
| --- | --- |
| `add` | Thêm vị thế mới (sau khi mua) |
| `remove` | Đóng một vị thế (sau khi bán) |
| `status` | Snapshot vị thế đang mở với giá hiện tại |
| `summary` | Báo cáo tổng hợp NAV, phân bổ ngành, top winners/losers |
| `closed` | Liệt kê giao dịch đã đóng |

### Lệnh mẫu

```bash
# Thêm vị thế VIC: 3300 CP @ 45,000 mua 2026-05-04
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py add \
  --symbol VIC --exchange hose \
  --shares 3300 --avg-price 45000 \
  --buy-date 2026-05-04 --sector "Bất động sản" \
  --state-dir state/vn_portfolio/

# Snapshot với giá hiện tại
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py status \
  --prices VIC:46500,HPG:28500,FPT:142000 \
  --state-dir state/vn_portfolio/

# Hoặc nạp giá từ file (output của vn-data-fetcher)
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py status \
  --prices-file reports/latest_prices.json \
  --state-dir state/vn_portfolio/

# Tóm tắt với phân bổ ngành
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py summary \
  --prices VIC:46500,HPG:28500,FPT:142000 \
  --account-size 1000000000 \
  --max-position-pct 10 --max-sector-pct 30 \
  --state-dir state/vn_portfolio/ \
  --output-dir reports/

# Đóng vị thế VIC
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py remove \
  --symbol VIC --close-price 47000 --close-date 2026-05-13 \
  --state-dir state/vn_portfolio/
```

### Pipeline với vn-data-fetcher

```bash
# Lấy giá đóng cửa mới nhất
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VIC,HPG,FPT --start 2026-05-12 --end 2026-05-13 \
  --output-dir /tmp/

# Tạo file prices.json (manual hoặc qua small helper script)
# Format: {"VIC": 46500, "HPG": 28500, "FPT": 142000}

# Run status với file prices
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py status \
  --prices-file /tmp/prices.json --state-dir state/vn_portfolio/
```

## State files

### `state/vn_portfolio/holdings.csv`

```csv
symbol,exchange,shares,avg_price,buy_date,sector,notes
VIC,hose,3300,45000,2026-05-04,Bất động sản,
HPG,hose,2000,28000,2026-05-06,Vật liệu,VCP breakout
FPT,hose,1000,140000,2026-04-20,Công nghệ,
```

### `state/vn_portfolio/closed.csv`

```csv
symbol,exchange,shares,avg_buy_price,buy_date,close_price,close_date,sector,gross_pnl_vnd,fees_vnd,tax_vnd,net_pnl_vnd,net_pnl_pct,hold_days
```

## Output Format

### Status

```json
{
  "schema_version": "1.0",
  "subcommand": "status",
  "as_of": "2026-05-13T08:00:00+07:00",
  "positions": [
    {
      "symbol": "VIC",
      "exchange": "hose",
      "sector": "Bất động sản",
      "shares": 3300,
      "avg_price": 45000,
      "current_price": 46500,
      "cost_basis_vnd": 148500000,
      "market_value_vnd": 153450000,
      "unrealized_gross_pnl_vnd": 4950000,
      "unrealized_after_fee_tax_pnl_vnd": 4356000,
      "unrealized_pnl_pct": 2.93,
      "hold_days": 9
    }
  ],
  "total_cost_basis_vnd": 396500000,
  "total_market_value_vnd": 410150000,
  "total_unrealized_pnl_vnd": 13650000,
  "total_unrealized_pnl_pct": 3.44
}
```

### Summary

Thêm:
- `nav_vnd` = `total_market_value_vnd` + `cash_vnd` (nếu cung cấp `--account-size`)
- `sector_breakdown`: dict ngành → %NAV
- `concentration_warnings`: list các mã / ngành vượt giới hạn
- `top_winners` / `top_losers`: top 3 mã theo unrealized %

## Nguyên tắc

1. **Sau phí + thuế là số thật** — Mọi P&L hiển thị có cả gross và net (sau phí 0.15% × 2 + thuế bán 0.1%)
2. **Không trộn realized và unrealized** — `closed.csv` cho realized, `holdings.csv` + giá hiện tại cho unrealized
3. **Cảnh báo concentration sớm** — Khi nhập lệnh `add`, kiểm tra ngay xem vị thế mới có vi phạm 10%/30% không
4. **Không tự động fetch giá** — User chủ động cung cấp; tách concern khỏi data layer
5. **Lưu CSV thay vì DB** — Đơn giản, có thể mở Excel, dễ backup, có thể edit thủ công khi cần
