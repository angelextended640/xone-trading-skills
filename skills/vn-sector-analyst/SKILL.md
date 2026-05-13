---
name: vn-sector-analyst
description: Phân tích rotation theo ngành VN-Index — tính return 5D/20D/60D theo ngành, relative strength vs VN-Index, top/bottom mã trong mỗi ngành. Banking ~30% trọng số, Bất động sản ~20%, khác hẳn cấu trúc Mỹ. Tiêu thụ output OHLCV từ vn-data-fetcher. Vietnam sector rotation analysis — sector returns over 5D/20D/60D, relative strength vs VN-Index, top/bottom symbols per sector. Banking dominates ~30% of VN-Index weight, very different from US sector composition.
---

# VN Sector Analyst — Phân tích rotation theo ngành VN

## Tổng quan

Phân tích **xu hướng dòng tiền theo ngành** trên VN-Index, sử dụng output OHLCV từ `vn-data-fetcher`.

VN-Index có cấu trúc **rất khác** S&P 500:

| Ngành VN-Index | Trọng số xấp xỉ | Tương đương Mỹ |
| --- | --- | --- |
| Banking | ~30% | ~13% S&P |
| Real Estate | ~20% | ~2% S&P |
| Materials | ~10% | ~2% S&P |
| Consumer Staples | ~7% | ~6% S&P |
| Technology | ~5% | ~30% S&P |

Hệ quả: rotation pattern không giống Mỹ. Khi **Banking** dẫn dắt, VN-Index có thể tăng mạnh dù các nhóm khác đi ngang. Khi **Real Estate** suy yếu (chu kỳ lãi suất), index dễ giảm sâu. Skill này giúp xác định nhóm đang **dẫn dắt** và **tụt hậu**.

## Khi nào dùng

- Hàng tuần / hàng ngày, kiểm tra ngành nào đang outperform
- Trước khi chọn mã cho swing trade — ưu tiên ngành có relative strength dương vs VN-Index
- Khi market regime đang chuyển — Banking thường dẫn vào uptrend, Real Estate dẫn ra
- Bổ trợ cho `vn-vcp-screener` / `vn-canslim-screener` (lọc thêm theo ngành dẫn dắt)

## Điều kiện tiên quyết

- Python 3.9+
- Đã chạy `vn-data-fetcher ohlcv --symbols ...` để có OHLCV
- Tham chiếu: `skills/vn-sector-analyst/references/vn_sector_mapping.json`

## Workflow

### Bước 1: Lấy OHLCV cho watchlist

```bash
# Fetch OHLCV cho toàn bộ universe trong sector mapping (mặc định ~80 mã)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VCB,BID,CTG,TCB,MBB,ACB,VPB,TPB,STB,HDB,VIC,VHM,VRE,NVL,KDH,DXG,PDR,DIG,HPG,HSG,NKG,DGC,MWG,DGW,PNJ,VNM,MSN,MCH,SAB,GAS,PLX,BSR,PVD,VJC,GMD,FPT,REE,SSI,VCI,HCM,BVH,DHG \
  --start 2026-02-01 --end 2026-05-13 \
  --output-dir reports/

# Cũng lấy VN-Index làm benchmark
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbol VNINDEX --start 2026-02-01 --end 2026-05-13 \
  --output-dir reports/
```

### Bước 2: Phân tích rotation

```bash
python3 skills/vn-sector-analyst/scripts/vn_sector_analyst.py \
  --ohlcv-file reports/vn_ohlcv_*_2026-05-13_*.json \
  --benchmark-file reports/vn_ohlcv_VNINDEX_2026-05-13_*.json \
  --output-dir reports/
```

Hoặc dùng fixture cho test offline:

```bash
python3 skills/vn-sector-analyst/scripts/vn_sector_analyst.py \
  --fixture skills/vn-sector-analyst/scripts/tests/fixtures/sample_batch.json \
  --output-dir reports/
```

### Bước 3: Đọc output

Skill trả về:

- **Bảng ngành xếp hạng:** sector → return_5D, return_20D, return_60D, relative_strength_vs_index
- **Top/bottom 3 mã trong mỗi ngành** theo return 20D
- **Rotation hints:** ngành nào vào uptrend (5D > 20D), ngành nào yếu dần (5D < 20D)
- **Cảnh báo:** nếu Banking weak (RS < −2%) và Real Estate weak → có thể market đang vào risk-off

## Output Format

```json
{
  "schema_version": "1.0",
  "as_of": "2026-05-13T10:00:00+07:00",
  "benchmark": "VNINDEX",
  "benchmark_returns": {"5D": 1.2, "20D": 3.5, "60D": -1.8},
  "sectors": [
    {
      "name": "Banking",
      "vn_index_weight_approx_pct": 30.0,
      "symbols_count": 9,
      "symbols_with_data": 8,
      "returns": {"5D": 2.4, "20D": 5.1, "60D": 1.2},
      "relative_strength": {"5D": 1.2, "20D": 1.6, "60D": 3.0},
      "trend_signal": "improving",
      "top_3_by_20D": [
        {"symbol": "MBB", "return_20D": 8.2},
        {"symbol": "TPB", "return_20D": 6.5},
        {"symbol": "VPB", "return_20D": 5.7}
      ],
      "bottom_3_by_20D": [...]
    }
  ],
  "rotation_hints": [
    {"type": "leader", "sector": "Banking", "msg": "Banking dẫn dắt (RS_20D +1.6, RS_5D +1.2)"},
    {"type": "laggard", "sector": "Real Estate", "msg": "Real Estate yếu (RS_20D −2.3)"}
  ],
  "regime_note": "Banking + Real Estate có cùng diễn biến mạnh — xu hướng tăng có cơ sở"
}
```

### Trend signals

| Signal | Điều kiện |
| --- | --- |
| `accelerating` | return_5D > return_20D > 0 |
| `improving` | return_5D > 0 và RS_5D > RS_20D |
| `stable` | giữa |
| `deteriorating` | return_5D < 0 và RS_5D < RS_20D |
| `falling` | return_5D < return_20D < 0 |

## Resources

- `references/vn_sector_mapping.json` — bảng phân ngành cho ~80 mã VN phổ biến nhất
- `scripts/vn_sector_analyst.py` — script chính
- Tham chiếu chéo: `skills/vn-data-fetcher/` (nguồn OHLCV)

## Nguyên tắc

1. **VN khác Mỹ về cấu trúc** — Banking 30% chứ không phải Tech 30%. Đừng máy móc áp khung S&P.
2. **Equal-weight mặc định trong ngành** — vì không có VN-Index weight chính xác cho mỗi mã, dùng equal-weight return per sector. Nếu cung cấp market cap, có thể chuyển sang cap-weight.
3. **Hợp tác với screeners** — Output của skill này nên feed vào `vn-vcp-screener` / `vn-breakout-trade-planner` để ưu tiên mã trong ngành dẫn dắt.
4. **Không tự fetch** — Skill chỉ phân tích; data fetch là việc của `vn-data-fetcher`. Pipeline rõ ràng giúp test và cache.
