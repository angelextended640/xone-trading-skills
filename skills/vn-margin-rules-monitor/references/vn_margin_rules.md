# Quy định Ký quỹ (Margin) tại thị trường Việt Nam — VN-specific calibration

> Quy tắc cơ sở (giờ phiên, T+2.5, lô 100, status flags, biên độ giá ±7/10/15%) đã được canonical hoá tại [`vn-market-mechanics/references/vn_trading_rules.md`](../../vn-market-mechanics/references/vn_trading_rules.md). File này tập trung vào **chi tiết margin** — phần mà các CTCK quyết định, không phải UBCKNN.

## Nguồn UBCKNN (baseline)

Tham chiếu canonical: `vn-market-mechanics/references/vn_trading_rules.md` mục margin.

Tóm tắt rules:

- Cổ phiếu **giao dịch < 6 tháng** kể từ ngày niêm yết HOSE/HNX → **không** được cấp margin.
- Cổ phiếu thuộc diện **Q-rated** (Kiểm soát / Hạn chế / Tạm ngừng / Cảnh báo) → bị **cắt margin ngay lập tức**.
- Báo cáo tài chính soát xét bán niên / kiểm toán năm có **ý kiến ngoại trừ hoặc lỗ** → bị cắt margin.
- Tỷ lệ ký quỹ ban đầu tối thiểu **50%** (CTCK cho vay tối đa 50% giá trị giao dịch).

## Tỷ lệ thực tế tại các CTCK

Mỗi CTCK tự quyết định tỷ lệ cho vay (`rate`) dựa trên danh sách UBCKNN nhưng:

- **Không vượt quá 50%** đối với cổ phiếu trên danh sách margin chuẩn
- **Mid-cap / Penny** thường 10-30% hoặc không cho vay
- **Blue-chip VN30** thường 40-50% (rate cao nhất)

| CTCK | Số mã chấp nhận margin (trung bình) | Đặc điểm |
| --- | --- | --- |
| TCBS | ~250 | List rộng nhất, Q-rated quy trình minh bạch |
| SSI | ~220 | Rate thấp hơn TCBS với mid-cap |
| VND | ~200 | Tier-3 nhiều, force sell aggressive |
| HCM | ~180 | Conservative, ít penny |
| VCI | ~150 | Premium broker, blue-chip only |

> **Lưu ý:** Số mã + rate thay đổi quarterly. CSV input cho `vn_margin_monitor.py record` phải lấy từ trang chính thức của CTCK hoặc bảng giá.

## Q-rated semantics

Cờ Q-rated bao gồm:

1. **Kiểm soát** (Q) — Vi phạm công bố thông tin, BCTC trễ
2. **Hạn chế** (G) — Lỗ 3 năm liên tiếp hoặc EPS âm
3. **Tạm ngừng** — Yếu tố nghiêm trọng, không giao dịch
4. **Cảnh báo** (W) — Lỗ 1 năm hoặc EPS thấp

→ Tất cả **không được cấp margin**. Nếu đang vay, CTCK gọi vốn về (force-sell).

## Hiện tượng Call Margin và Force Sell — rủi ro VN-specific

- **Biên độ giá** (HOSE ±7%, HNX ±10%, UPCOM ±15%) → khi cổ phiếu giảm sàn liên tục, position bị âm nhanh → CTCK gọi margin trong 1-2 ngày.
- **Stop-loss "tự động" không tồn tại** ở hầu hết CTCK truyền thống → call margin chỉ có thể bằng nhân viên hỗ trợ + bán manual.
- **Call chéo** — khi 1 mã bị kẹt thanh khoản, CTCK có quyền bán **các mã khác** trong danh mục để thu hồi nợ. → Risk cao nhất với portfolio concentrated.
- **Cổ phiếu Q-rated đột ngột** — vi phạm BCTC quý có thể bị cắt margin ngay; toàn bộ vị thế margin của mã đó phải đóng trong 3-5 ngày.

## CSV schema cho `vn_margin_monitor.py record`

```csv
symbol,rate,note,as_of_date
FPT,50,,2026-05-13
VIC,30,Q-rated,2026-05-13
HPG,40,,2026-05-13
VHM,0,Suspended margin,2026-05-13
```

| Cột | Bắt buộc | Mô tả |
| --- | --- | --- |
| `symbol` | có | Mã cổ phiếu |
| `rate` | có | Tỷ lệ cho vay % (0-50). `0` = không cho vay |
| `note` | tuỳ chọn | Note tự do; nếu chứa "Q-rated", subcommand `check --warn-q-rated` sẽ surface warning |
| `as_of_date` | tuỳ chọn | Ngày snapshot. Mặc định = hôm nay (Asia/Ho_Chi_Minh) |

## Tham chiếu vn-market-mechanics

- [`vn_trading_rules.md`](../../vn-market-mechanics/references/vn_trading_rules.md) — sessions, status flags, T+2.5
- [`vn_price_limits_orders.md`](../../vn-market-mechanics/references/vn_price_limits_orders.md) — biên độ giá driving force-sell mechanic
- [`vn_fees_and_taxes.md`](../../vn-market-mechanics/references/vn_fees_and_taxes.md) — broker fee context

## Cảnh báo skill use

- Skill này **chỉ track**, không **dự báo**. Khi CTCK ra thông báo cắt margin, dùng `record` để cập nhật trạng thái mới.
- Lịch sử thay đổi qua thời gian: dùng subcommand `history` (snapshot mỗi lần `record` → so sánh diff).
