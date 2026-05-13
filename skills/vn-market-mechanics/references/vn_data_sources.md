# Nguồn dữ liệu — TTCK Việt Nam

**Last updated:** 2026-05-12

## 1. Thư viện chính: `vnstock` (open source)

**Đây là nguồn dữ liệu chính** cho tất cả skill `vn-*` trong repository này.

### Cài đặt

```bash
pip install vnstock
# Hoặc qua optional dependency:
pip install -e ".[vn]"
```

### Tính năng

`vnstock` là thư viện Python tổng hợp các API miễn phí của TCBS, SSI, VCI, VND và một số nguồn khác. Hỗ trợ:

- **OHLCV lịch sử** (cổ phiếu, chỉ số, phái sinh)
- **Bảng giá real-time** (gần real-time, có độ trễ vài giây)
- **Báo cáo tài chính** (BCTC, kết quả kinh doanh)
- **Cổ tức và sự kiện** (ex-date, ratio)
- **Sở hữu khối ngoại** và NAV ETF
- **Chỉ số tài chính** (P/E, P/B, ROE, EPS)
- **Tin tức** từ CafeF, Vietstock
- **Giao dịch khối** (foreign net flow, prop trading flow)

### Ví dụ sử dụng cơ bản

```python
from vnstock import Vnstock

stock = Vnstock().stock(symbol='VIC', source='VCI')

# OHLCV
df = stock.quote.history(start='2025-01-01', end='2026-05-12', interval='1D')

# Báo cáo tài chính
bs = stock.finance.balance_sheet(period='quarter')
income = stock.finance.income_statement(period='quarter')

# Chỉ số
ratios = stock.finance.ratio(period='quarter')

# Cổ tức
dividends = stock.company.dividends()
```

### Hạn chế

- API nguồn (TCBS/SSI/VCI) có thể **rate-limit** ở cấp IP
- Một số endpoint có **độ trễ T+1** (kết thúc phiên hôm nay mới có data)
- **Không có** orderbook tick-by-tick real-time
- Chất lượng data phụ thuộc vào nguồn upstream — đôi khi có lỗi cho mã hiếm giao dịch (UPCOM nhỏ)
- Dữ liệu trước 2015 có thể thiếu cho một số mã

### Mẫu retry-on-rate-limit

```python
import time
from vnstock import Vnstock

def fetch_with_retry(symbol, max_retries=3, backoff=5):
    for attempt in range(max_retries):
        try:
            return Vnstock().stock(symbol=symbol, source='VCI').quote.history(...)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(backoff * (2 ** attempt))
```

## 2. Nguồn thay thế (fallback)

### Khi `vnstock` không có data

| Nguồn | Loại data | Cách dùng |
| --- | --- | --- |
| **FireAnt** | Bảng giá, OHLCV, fundamentals | https://fireant.vn/ — API public (cần inspect network) |
| **CafeF** | Bảng giá, tin tức, BCTC | https://cafef.vn/ — scraping |
| **VietStock** | Bảng giá, screener, BCTC | https://vietstock.vn/ — đăng ký account |
| **SSI iBoard / FastConnect** | Real-time, official | Cần tài khoản SSI + đăng ký API |
| **TCBS API** | Real-time | Cần tài khoản TCBS |
| **DNSE API** | Real-time | Cần tài khoản DNSE |

### Khi cần data quốc tế (USD pair, MSCI, v.v.)

- Yahoo Finance (`yfinance`) — dùng cho ticker quốc tế ghép VN (như "VNM.HM" cho HOSE qua Yahoo nếu có)
- Refinitiv / Bloomberg — chỉ áp dụng cho tổ chức

## 3. Quy ước skill `vn-*` về data sources

1. **Mặc định dùng `vnstock`** trong mọi script `vn-*/scripts/`
2. **Có cờ `--data-source`** cho phép user chọn `vci | tcbs | ssi` (tham số `source` của vnstock)
3. **Fallback graceful:** Nếu `vnstock` không có data (lỗi rate-limit, mã không tồn tại, BSE), báo lỗi rõ ràng và đề xuất nguồn thay thế thủ công
4. **Cache local:** Lưu OHLCV lịch sử dưới `state/vn_market_data/<symbol>_<interval>.parquet` để tránh fetch lại
5. **Phải có `--fixture` mode** cho test offline (đọc data mẫu từ `tests/fixtures/`)

## 4. Quy ước data layer cho skill VN

### Header chuẩn cho mỗi script `vn-*/scripts/*.py` có gọi vnstock

```python
"""<Tên skill> — <Mô tả ngắn>.

Data source: vnstock (https://github.com/thinh-vu/vnstock).
Default upstream: VCI. Override via --data-source.
Offline test: pass --fixture <path-to-parquet>.
"""
```

### Convention cho symbol

- Cổ phiếu HOSE/HNX/UPCOM: **3 ký tự** in hoa (VIC, HPG, VNM, MWG)
- ETF: 3-5 ký tự (E1VFVN30, FUEVFVND)
- Chỉ số: VNINDEX, VN30, HNX-INDEX, HNX30, UPCOM-INDEX
- Phái sinh: VN30F1M (front month), VN30F2M (next month), VN30F1Q, VN30F2Q

### Convention cho giá

- **Đơn vị: VND** trong mọi output và parameter
- Hiển thị với dấu phân cách hàng nghìn (45,500 VND)
- Trong JSON: lưu dưới dạng integer (45500) hoặc float (45500.0); **không** dùng string

### Convention cho timezone

- Mọi timestamp **UTC+7 (Asia/Ho_Chi_Minh)**
- Trong JSON: ISO 8601 với offset rõ ràng (`2026-05-12T14:30:00+07:00`)
