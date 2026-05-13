---
name: vn-market-mechanics
description: Cơ chế thị trường chứng khoán Việt Nam — HOSE/HNX/UPCOM, biên độ giá ±7%/±10%/±15%, T+2.5, lô 100, room ngoại, phí giao dịch, thuế. Kích hoạt khi câu hỏi liên quan đến luật/quy tắc/cơ chế giao dịch CK Việt Nam, hoặc khi một skill VN khác cần tham chiếu chuẩn. Vietnam stock market mechanics reference — HOSE/HNX/UPCOM exchanges, ±7%/±10%/±15% daily price limits, T+2.5 settlement, lot size 100, foreign room, fees, taxes. Trigger when user asks about VN market trading rules, or when another vn-* skill needs canonical reference.
---

# VN Market Mechanics — Kiến thức nền thị trường CK Việt Nam

## Tổng quan

Đây là **skill tham chiếu (knowledge-only)** — không có script chạy. Các skill `vn-*` khác sẽ đọc các file trong `references/` để áp dụng đúng quy tắc thị trường Việt Nam khi thực hiện phân tích, sàng lọc, hoặc lập kế hoạch giao dịch.

## Khi nào dùng

Tải skill này khi:

- Người dùng hỏi về cơ chế giao dịch CK Việt Nam (biên độ, T+2.5, lô, room ngoại, phí, thuế)
- Một skill `vn-*` khác (như `vn-position-sizer`, `vn-portfolio-manager`) cần tham chiếu chuẩn về quy tắc thị trường
- Cần xác thực giá trần/sàn, lot size, hoặc các giới hạn pháp lý trước khi đề xuất giao dịch

## Workflow

1. Đọc file tham chiếu phù hợp trong `references/` tùy theo câu hỏi:
   - Quy tắc giao dịch chung → `vn_trading_rules.md`
   - Biên độ giá và lệnh → `vn_price_limits_orders.md`
   - Phí và thuế → `vn_fees_and_taxes.md`
   - Room ngoại → `vn_foreign_ownership.md`
   - Nguồn dữ liệu (vnstock) → `vn_data_sources.md`
2. Áp dụng các con số chính xác trong câu trả lời hoặc tính toán
3. Nếu có thay đổi gần đây từ UBCKNN/Sở GDCK, **luôn ghi rõ ngày tham chiếu** của tài liệu và khuyến nghị người dùng kiểm tra lại nguồn chính thức

## Nguồn chính thức (để cập nhật khi cần)

- Ủy ban Chứng khoán Nhà nước (UBCKNN): https://www.ssc.gov.vn/
- Sở GDCK TP.HCM (HOSE): https://www.hsx.vn/
- Sở GDCK Hà Nội (HNX): https://www.hnx.vn/
- Tổng Công ty Lưu ký và Bù trừ CK (VSDC): https://www.vsd.vn/

## Tài nguyên (`references/`)

- `vn_trading_rules.md` — Quy tắc giao dịch, giờ giao dịch, phiên, T+
- `vn_price_limits_orders.md` — Biên độ ±7/10/15%, loại lệnh (ATO/LO/MP/ATC), bước giá
- `vn_fees_and_taxes.md` — Phí môi giới, phí UBCKNN, thuế bán 0.1%, thuế cổ tức 5%
- `vn_foreign_ownership.md` — Room ngoại, danh mục đặc biệt
- `vn_data_sources.md` — Thư viện vnstock, các nguồn dữ liệu thay thế

## Ghi chú quan trọng

- Các con số trong tài liệu là **giá trị danh nghĩa theo quy định** ở thời điểm cập nhật cuối (`Last updated:` ở đầu mỗi file)
- Quy định thị trường có thể thay đổi (ví dụ: dự kiến chuyển sang KRX và rút ngắn T+1 trong tương lai). Luôn xác minh với nguồn chính thức trước quyết định thực tế
- Các skill `vn-*` khác **phải** trích dẫn file tham chiếu cụ thể (ví dụ: "theo `vn_fees_and_taxes.md`") khi áp dụng quy tắc, không tự suy đoán
