---
name: vn-data-fetcher
description: Lấy dữ liệu thị trường chứng khoán Việt Nam qua thư viện vnstock — OHLCV, thông tin niêm yết, lịch sử cổ tức, fundamentals (P/E, P/B, ROE, EPS, payout), và snapshot khối ngoại. Cache local dưới state/vn_market_data/. Hỗ trợ fixture mode cho test offline. Kích hoạt khi cần lấy giá lịch sử, thông tin niêm yết, cổ tức, hoặc tỷ số tài chính cho cổ phiếu HOSE/HNX/UPCOM. Vietnam stock data fetcher — OHLCV, info, dividends, fundamentals (ratios), foreign-flow snapshot via vnstock.
---

# VN Data Fetcher — Lấy dữ liệu thị trường CK Việt Nam

## Tổng quan

Wrapper CLI quanh thư viện open-source `vnstock` để lấy:

- **OHLCV lịch sử** (cổ phiếu, chỉ số, ETF) — `ohlcv` subcommand
- **Thông tin niêm yết** (ngành, vốn hoá, ngày niêm yết) — `info` subcommand
- **Lịch sử cổ tức** (cash + stock dividend) — `dividends` subcommand
- **Fundamentals** (P/E, P/B, ROE, EPS, payout ratio, ...) — `fundamentals` subcommand
- **Foreign flow snapshot** (point-in-time, không có daily series) — `foreign-flow` subcommand

Mỗi lệnh có **cache CSV/parquet** dưới `state/vn_market_data/` để tránh fetch lại data đã có. Có **fixture mode** để test offline mà không cần kết nối Internet hoặc vnstock.

## Khi nào dùng

- Một skill VN khác cần OHLCV cho một mã (vd: `vn-vcp-screener`, `vn-breakout-trade-planner`)
- Cần thông tin định danh cho mã: sàn, ngành, room ngoại, số CP lưu hành
- Cần series foreign flow cho phân tích sentiment khối ngoại
- User hỏi "giá đóng cửa của VIC 30 phiên gần nhất", "khối ngoại mua/bán ròng FPT tháng trước"

**KHÔNG** dùng skill này để:
- Lập kế hoạch giao dịch — dùng `vn-position-sizer` hoặc `vn-breakout-trade-planner`
- Phân tích room ngoại theo watchlist — dùng `vn-foreign-room-tracker` (sắp ra mắt)

## Điều kiện tiên quyết

- Python 3.9+
- `vnstock>=3.0` (cài qua `pip install -e ".[vn]"` hoặc `pip install vnstock`)
- Kết nối Internet (trừ khi dùng `--fixture`)
- Pandas (transitively từ vnstock)

## Workflow

### Bước 1: Xác định subcommand

| Subcommand | Mục đích |
| --- | --- |
| `ohlcv` | Open/High/Low/Close/Volume theo ngày, tuần, tháng, hoặc intraday |
| `info` | Thông tin niêm yết (sàn, ngành, vốn hoá, số CP lưu hành) |
| `dividends` | Lịch sử cổ tức (cash + stock). Tự động phân loại type, convert % → VND/CP |
| `fundamentals` | Báo cáo tỷ số tài chính theo `quarter` hoặc `year` (P/E, P/B, ROE, EPS, payout) |
| `foreign-flow` | Snapshot khối ngoại (point-in-time only — không có daily series) |

> **Lưu ý:** `foreign-flow` chỉ trả snapshot tại thời điểm gọi. vnstock không cung cấp daily-series endpoint thống nhất cho khối ngoại. Để xây history theo ngày, dùng `vn-foreign-room-tracker record` với CSV nhập thủ công.

### Bước 2: Chạy lệnh

```bash
# OHLCV: 1 mã, 1 ngày tròn năm
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbol VIC --start 2025-05-01 --end 2026-05-12 \
  --interval 1D --source VCI \
  --output-dir reports/

# OHLCV: nhiều mã batch
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VIC,HPG,VNM,FPT \
  --start 2026-01-01 --end 2026-05-12 \
  --output-dir reports/

# Info công ty
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py info \
  --symbol VIC --source VCI \
  --output-dir reports/

# Foreign flow snapshot (point-in-time)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py foreign-flow \
  --symbol VIC \
  --output-dir reports/

# Lịch sử cổ tức (cash + stock)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py dividends \
  --symbol VIC --source VCI \
  --output-dir reports/

# Fundamentals theo quý (P/E, P/B, ROE, EPS, payout)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py fundamentals \
  --symbol VIC --period quarter \
  --output-dir reports/

# Fundamentals theo năm
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py fundamentals \
  --symbol VIC --period year \
  --output-dir reports/

# Test offline với fixture
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbol VIC --start 2026-05-01 --end 2026-05-12 \
  --fixture tests/fixtures/vic_daily.csv \
  --output-dir reports/

# Skip cache (lấy data tươi)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbol VIC --start 2026-05-01 --end 2026-05-12 \
  --no-cache --output-dir reports/
```

### Bước 3: Đọc output

Mỗi lệnh xuất hai file:

- `<symbol>_<subcommand>_<timestamp>.json` — metadata + dữ liệu (record-oriented)
- `<symbol>_<subcommand>_<timestamp>.csv` (cho ohlcv) — CSV phẳng dễ đọc

Cache lưu tại `state/vn_market_data/<symbol>_<source>_<interval>.csv` — không có timestamp; lần fetch sau cùng phủ lên (full refresh).

### Bước 4: Báo cáo cho user

Tóm tắt số dòng, khoảng ngày, mã, và ghi chú nếu data thiếu hoặc có gap.

## Output Format

### OHLCV JSON

```json
{
  "schema_version": "1.0",
  "subcommand": "ohlcv",
  "symbol": "VIC",
  "source": "VCI",
  "interval": "1D",
  "range": {
    "start": "2026-05-01",
    "end": "2026-05-12"
  },
  "row_count": 7,
  "fetched_at": "2026-05-13T07:45:00+07:00",
  "cache_status": "miss",
  "data": [
    {"time": "2026-05-04", "open": 217.0, "high": 220.0, "low": 204.0, "close": 212.0, "volume": 3884000},
    ...
  ]
}
```

### Info JSON

```json
{
  "schema_version": "1.0",
  "subcommand": "info",
  "symbol": "VIC",
  "source": "VCI",
  "exchange": "HOSE",
  "industry": "Bất động sản",
  "listed_date": "2007-09-19",
  "outstanding_shares": 3823661561,
  "market_cap_vnd": null
}
```

## Resources

- `scripts/vn_data_fetcher.py` — CLI chính với các subcommand
- `scripts/tests/` — pytest suite + fixtures CSV
- Tham chiếu: `skills/vn-market-mechanics/references/vn_data_sources.md` cho quy ước data sources và conventions

## Lưu ý vận hành

1. **Rate limit:** Các nguồn upstream (TCBS/VCI/SSI) có thể rate-limit. Cache hợp lý giúp giảm tải. Nếu gặp lỗi rate-limit, retry sau 30-60s.
2. **Độ trễ T+0:** Một số endpoint có data của phiên hôm nay chỉ vào cuối ngày. Không kỳ vọng intraday real-time chính xác.
3. **Đơn vị giá:** vnstock thường trả giá theo **nghìn VND** (ví dụ `217.0` = 217,000 VND/CP) — script ghi nhận thông tin này trong metadata.
4. **Mã hợp lệ:** Cổ phiếu HOSE/HNX/UPCOM dùng 3-5 ký tự in hoa. Chỉ số: `VNINDEX`, `VN30`, `HNX-INDEX`. Phái sinh: `VN30F1M`, `VN30F2M`.
5. **Fixture cho test:** Định dạng CSV phải có cột `time, open, high, low, close, volume`. Có thể tạo từ output cache cũ.

## Nguyên tắc

1. **Cache đầu tiên** — tránh fetch lại data đã có. User dùng `--no-cache` khi cần data tươi.
2. **Fixture cho test** — mọi test offline phải dùng `--fixture`, không gọi vnstock thật.
3. **Log rõ ràng** — báo cho user biết hit cache hay miss, có gap dữ liệu không.
4. **Fail fast** — nếu vnstock không cài hoặc symbol sai, báo lỗi rõ ràng và dừng.
