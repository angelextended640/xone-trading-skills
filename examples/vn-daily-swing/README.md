# VN Daily Swing — End-to-end workflow example

> Một ví dụ runnable cho thấy 9 skill `vn-*` kết hợp thành workflow giao dịch swing hàng ngày trên TTCK Việt Nam.

## Bối cảnh giả định

- **Trader:** cá nhân, tài khoản 1 tỷ VND
- **Style:** Core + Satellite, swing 1-8 tuần
- **CTCK:** VPS (phí 0.15% online)
- **Thời gian:** ngày 2026-05-13 (thứ Tư), trước phiên 09:00 ICT
- **Watchlist (universe):** VN30 + một số mid-cap thanh khoản tốt

## Workflow (12 bước)

### Bước 0: Setup (chỉ làm 1 lần)

```bash
# Cài deps
pip install -e ".[dev,vn]"

# Tạo state dirs
mkdir -p state/vn_portfolio state/vn_foreign_room state/vn_market_data
mkdir -p reports
```

---

### Bước 1: News scan trước phiên (10 phút)

Hỏi Claude trong Claude Code:

```
Tôi cần news brief VN cho hôm nay. Có gì đáng chú ý từ tối qua đến sáng nay?
```

→ Claude trigger `vn-news-analyst`, WebSearch CafeF/Vietstock/NDH, output:

```
Bài 1: SBV giữ nguyên lãi suất điều hành, OMO bơm ròng 15,000 tỷ
  Source: CafeF — 2026-05-13
  Impact: + Banking (thanh khoản tăng), + Real Estate (tâm lý)
  Affected: VCB, BID, CTG (positive), VHM, NVL (positive nhẹ)

Bài 2: Khối ngoại mua ròng 850 tỷ phiên hôm qua, tập trung FPT, MWG
  Source: Vietstock — 2026-05-12 cuối phiên
  Impact: ++ FPT, MWG, ngành công nghệ + bán lẻ
  Foreign room FPT đầy 100% sau phiên
```

---

### Bước 2: Fetch OHLCV cho universe (5 phút)

```bash
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbols VCB,BID,CTG,TCB,MBB,VIC,VHM,VRE,HPG,HSG,MWG,FPT,VNM,MSN,GAS,PLX,SSI,VCI \
  --start 2026-02-13 --end 2026-05-12 \
  --output-dir reports/

# Fetch benchmark riêng (VN-Index)
python3 skills/vn-data-fetcher/scripts/vn_data_fetcher.py ohlcv \
  --symbol VNINDEX --start 2026-02-13 --end 2026-05-12 \
  --output-dir reports/
```

Output: `reports/vn_ohlcv_<symbols>_2026-05-13_HHMMSS.json` (batch) + `vn_ohlcv_VNINDEX_*.json`.

---

### Bước 3: Sector rotation analysis (1 phút)

```bash
python3 skills/vn-sector-analyst/scripts/vn_sector_analyst.py \
  --ohlcv-glob 'reports/vn_ohlcv_*2026-05-13*.json' \
  --benchmark-file reports/vn_ohlcv_VNINDEX_*.json \
  --windows 5,20,60 \
  --output-dir reports/
```

Output (rút gọn):

```
Sector              5D      20D    60D     RS_20D    Signal
Banking            +1.2%   +3.5%  +2.1%   +1.5     improving
Real Estate        +0.8%   +2.1%  -1.5%   +0.1     stable
Technology         +2.8%   +5.4%  +4.2%   +3.4     accelerating
Consumer Disc      +0.5%   +1.2%  -0.5%   -0.8     deteriorating
...

Rotation hints:
  - Technology dẫn dắt (RS_20D +3.4)
  - Banking improving (RS_20D +1.5)
  - Consumer Discretionary yếu

Regime: Banking + Real Estate có cùng diễn biến tích cực — xu hướng tăng có cơ sở
```

---

### Bước 4: Foreign room snapshot (3 phút)

Nhập room ngoại từ bảng giá CTCK (manual hoặc copy-paste):

```bash
cat > /tmp/today_room.csv <<'EOF'
symbol,room_total,room_used,room_remaining
FPT,1456789012,1456789012,0
MWG,1234567890,1230000000,4567890
VIC,3823661561,3812000000,11661561
VCB,5067900000,1520370000,3547530000
HPG,5814785700,2300000000,3514785700
EOF

python3 skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py record \
  --input /tmp/today_room.csv \
  --as-of 2026-05-13 \
  --state-dir state/vn_foreign_room/

python3 skills/vn-foreign-room-tracker/scripts/vn_foreign_room.py report \
  --state-dir state/vn_foreign_room/ \
  --lookback-days 5 \
  --output-dir reports/
```

Output:

```
Báo cáo 2026-05-13 (so với 2026-05-08):
  FPT      100.00% Δ+0.04%  [full]
  MWG       99.63% Δ+0.85%  [high_usage]
  VIC       99.69% Δ+0.12%  [full]
  VCB       30.00% Δ+0.00%  [normal]  (Banking room 30% limit)
  HPG       39.55% Δ+1.20%  [normal]

Alerts:
  ⚠️ MWG room used 99.63%, gần đầy — foreign demand mạnh
```

---

### Bước 5: Identify breakout candidate (10 phút)

Dựa trên bước 3 và 4:
- **Ngành dẫn dắt:** Technology (RS_20D +3.4)
- **Foreign hot:** FPT (room full), MWG (gần full)
- **News positive:** FPT đang được nước ngoài mua mạnh

→ **Candidate: FPT** (giả định đã quan sát thấy breakout pattern trên chart)

---

### Bước 6: Build trade plan với guardrails VN (3 phút)

```bash
python3 skills/vn-breakout-trade-planner/scripts/vn_breakout_planner.py \
  --account-size 1000000000 \
  --symbol FPT --exchange hose \
  --setup-type breakout \
  --pivot 142000 --stop 135000 \
  --risk-pct 1.0 \
  --buy-date 2026-05-13 \
  --sector-analysis-file reports/vn_sector_analysis_2026-05-13_*.json \
  --foreign-room-file reports/vn_foreign_room_report_2026-05-13_*.json \
  --output-dir reports/
```

Output:

```
=== FPT (HOSE) — breakout ===
Pivot:           142,000 VND
Stop:            135,000 VND  (risk/share 7,000)
Shares:              1,400 CP
Position:      198,800,000 VND  (19.88% of account — within 10%? No → warning)
Risk:           9,800,000 VND  (0.98%)
Trần / Sàn:   151,900 / 132,100 (7.0%)

Targets:
   T1 (1.0R):    149,000 VND (33% size)
   T2 (2.0R):    156,000 VND (33% size) ← BLOCKED by ceiling 151,900!
   T3 (3.0R):    163,000 VND (34% size) ← BLOCKED

T+2.5: 2026-05-15 chiều
Round-trip cost: 0.4%

Context:
  Sector Technology: leader (RS_20D +3.4)
  Foreign room: full (100.0% used)

⚠️ Cảnh báo:
  - Position chiếm 19.88% NAV, vượt giới hạn 10% — giảm size
  - Target T2 và T3 vượt giá trần phiên đầu — chỉ T1 đạt được intraday
```

→ **Quyết định:** Giảm size xuống 700 CP (vẫn risk 1% nhưng vị thế chỉ 10% NAV).

---

### Bước 7: Check fee + tax cost trước khi đặt lệnh (1 phút)

```bash
python3 skills/vn-tax-fee-calculator/scripts/vn_tax_fee_calculator.py trade \
  --shares 700 --entry 142000 --exit 149000 \
  --broker vps \
  --output-dir reports/
```

Output:

```
=== Trade Cost — VPS ===
Entry value : 99,400,000 VND
Exit value  : 104,300,000 VND
Buy fee     : 149,100 VND
Sell fee    : 156,450 VND
Sell tax    : 104,300 VND
Total cost  : 409,850 VND (0.412%)
Gross P&L   : 4,900,000 VND
Net P&L     : 4,490,150 VND (4.52%)
Break-even  : 142,594 VND (+0.418%)
```

Hoặc so sánh với các CTCK khác nếu chưa chọn:

```bash
python3 skills/vn-tax-fee-calculator/scripts/vn_tax_fee_calculator.py compare \
  --shares 700 --entry 142000 --exit 149000 \
  --brokers vps,ssi,tcbs,dnse \
  --output-dir reports/
```

---

### Bước 8: Đặt lệnh tại CTCK

(Bước thủ công — đặt lệnh BO 700 CP FPT giá 142,000 ở VPS app)

Khi khớp: 700 CP @ 142,000.

---

### Bước 9: Ghi nhận vào portfolio (1 phút)

```bash
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py add \
  --symbol FPT --exchange hose \
  --shares 700 --avg-price 142000 \
  --buy-date 2026-05-13 --sector "Công nghệ" \
  --state-dir state/vn_portfolio/ \
  --output-dir reports/
```

---

### Bước 10: Cuối phiên — snapshot portfolio

```bash
# Giả định FPT đóng cửa 144,000 (target chưa đạt nhưng setup OK)
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py summary \
  --prices "FPT:144000" \
  --account-size 1000000000 \
  --max-position-pct 10 --max-sector-pct 30 \
  --state-dir state/vn_portfolio/ \
  --output-dir reports/
```

Output:

```
Vị thế mở: 1
Tổng cost basis: 99,400,000 VND
Tổng market value: 100,800,000 VND
P&L chưa thực hiện: 1,400,000 VND (1.41%)

Top winners:
  FPT: 1.41%
```

---

### Bước 11: Plan ngày mai

- T+1 (2026-05-14): CP chưa về tài khoản, **không bán được**
- T+2 chiều (2026-05-15): CP về, có thể bán nếu cần
- Set alert giá tại CTCK: FPT < 135,000 → cảnh báo (intraday stop sẽ chỉ thực hiện được từ chiều 2026-05-15)

---

### Bước 12: Cuối tuần — review

```bash
# Xem realized trades trong tuần
python3 skills/vn-portfolio-manager/scripts/vn_portfolio_manager.py closed \
  --state-dir state/vn_portfolio/ \
  --output-dir reports/

# Re-run sector analysis cho tuần tới
python3 skills/vn-sector-analyst/scripts/vn_sector_analyst.py \
  --ohlcv-glob 'reports/vn_ohlcv_*2026-05-17*.json' \
  --benchmark-file reports/vn_ohlcv_VNINDEX_*.json \
  --output-dir reports/
```

---

## File trong thư mục này

- `README.md` — file này, workflow chi tiết
- `sample_inputs/` — fixture data dùng cho demo offline (xem dưới)
- `sample_reports/` — output mẫu từ workflow (rút gọn)
- `run_demo.sh` — script chạy toàn bộ workflow với sample data

## Chạy demo offline

```bash
cd examples/vn-daily-swing
bash run_demo.sh
```

Demo sẽ chạy bước 2-7 và 9-10 (skip news scan + manual order) với dữ liệu fixture.

## Lưu ý quan trọng

1. **Đây là ví dụ giáo dục** — không phải khuyến nghị mua FPT hoặc bất kỳ mã cụ thể.
2. **Số liệu giả định** — Giá, room ngoại, sector data trong demo là tổng hợp / synthetic.
3. **Workflow thủ công** — Trader vẫn ra quyết định cuối cùng tại mỗi bước, không tự động.
4. **Phù hợp swing** — Workflow này cho timeframe 1-8 tuần. **Không phù hợp** scalping/intraday do T+2.5.
5. **Adapt theo broker** — Phí trong ví dụ giả định VPS 0.15%; điều chỉnh nếu dùng CTCK khác.
