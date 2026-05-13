# Room ngoại — Giới hạn sở hữu nước ngoài

**Last updated:** 2026-05-12
**Nguồn:** UBCKNN, HOSE/HNX công bố hàng ngày

## 1. Khái niệm

"**Room ngoại**" (foreign room) là **tỷ lệ tối đa nhà đầu tư nước ngoài được sở hữu** trên tổng cổ phiếu lưu hành của một công ty đại chúng. Khi room đầy, nhà đầu tư nước ngoài **không thể mua thêm** cho đến khi có người ngoại bán ra (giải phóng room).

## 2. Mức room ngoại theo ngành

| Ngành/loại doanh nghiệp | Room ngoại tối đa |
| --- | --- |
| Doanh nghiệp niêm yết thông thường | **49%** (mặc định) |
| Doanh nghiệp đã nới room | **100%** (sau khi ĐHCĐ thông qua) |
| Ngân hàng thương mại cổ phần | **30%** |
| Doanh nghiệp ngành có điều kiện (vận tải hàng không, viễn thông, v.v.) | Theo cam kết WTO/CPTPP, thường **30-49%** |
| Doanh nghiệp 100% vốn nhà nước niêm yết (BIDV, VCB, v.v.) | Theo quy định riêng |

## 3. Cách kiểm tra room ngoại

- **HOSE:** https://www.hsx.vn/Modules/Listed/Web/SymbolView (xem mục Tỷ lệ sở hữu nước ngoài)
- **vnstock:** `from vnstock import Quote; Quote(symbol='VIC').history(...)` — cũng cung cấp foreign holding data
- **Bảng giá CTCK:** Mọi bảng giá hiển thị 3 cột "Room ngoại còn lại / Đã sở hữu / Tổng room"
- **API:** FireAnt, CafeF, SSI iBoard đều có endpoint trả về room còn lại theo ngày

## 4. Tại sao quan trọng cho swing trader Việt Nam

### Tín hiệu sentiment

- **Khối ngoại mua ròng** cổ phiếu blue-chip thường có sức tác động lớn lên giá (đặc biệt với VN30)
- **Khối ngoại bán ròng** liên tục là tín hiệu áp lực cung dài hạn
- **Room đầy** (foreign ownership = 100% room) cho thấy nhu cầu nước ngoài cao — thường hỗ trợ giá

### Đặc biệt với cổ phiếu "hot" của khối ngoại

Các mã thường có **room đầy thường xuyên** (theo thời điểm 2025-2026):
- VIC, VHM, VRE (Vingroup)
- FPT, MWG, PNJ
- VNM, MSN, GAS (blue chip tiêu dùng/năng lượng)
- Ngành ngân hàng: ACB, MBB, TPB, STB (room 30%)

Khi một mã **vừa giải phóng room** (nước ngoài bán ra), cầu mua mới có thể đẩy giá tăng nhanh.

### Hệ quả thực tiễn

1. Khi sàng lọc cổ phiếu, theo dõi **giao dịch khối ngoại ròng (Net Foreign Volume)** trong 5/10/20 phiên
2. Cổ phiếu room đầy + khối ngoại mua tiếp = cầu cao bất thường → tín hiệu tốt
3. Cổ phiếu khối ngoại bán mạnh + room nhả ra = áp lực giảm

## 5. Hệ quả cho các skill VN

### `vn-foreign-room-tracker` (Phase 2)
- Theo dõi room ngoại còn lại theo ngày cho danh mục mã
- Cảnh báo khi room đầy / sắp đầy / đột nhiên giải phóng

### `vn-sector-analyst`
- Phân tích dòng vốn ngoại vào/ra theo ngành mỗi tuần
- Banking thường có dòng vốn riêng do room 30%

### `vn-vcp-screener` / breakout screeners
- Lọc bổ sung: chỉ chọn mã có khối ngoại mua ròng trong 20 phiên gần nhất

## 6. Ghi chú dữ liệu

- Số liệu room ngoại cập nhật **cuối ngày T** (không real-time intraday cho người dùng thông thường)
- Một số tổ chức có quyền giao dịch khối lượng lớn qua phiên thoả thuận, **không** tính ngay vào room trong ngày
- Chính phủ và Sở GDCK có thể điều chỉnh room cho ngành đặc biệt — cập nhật từ nguồn chính thức khi cần
