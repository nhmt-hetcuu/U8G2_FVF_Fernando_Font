# FVF Fernando Font cho U8g2 / ST75256

Font bitmap tự chế, hỗ trợ đầy đủ tiếng Việt có dấu, dùng trực tiếp với
`u8g2.drawPixel()` — **không phụ thuộc font engine của U8g2**, nên chạy
được với bất kỳ driver màn hình nào expose được hàm `drawPixel(x, y)`
(không riêng gì ST75256). Font được trích xuất tự động từ file TTF
"FVF Fernando 08" bằng Python + Pillow .

> ⚠️ **REPO NÀY LÀ PRIVATE, KHÔNG PUBLISH CÔNG KHAI.** Xem mục
> [Bản quyền font nguồn](#bản-quyền-font-nguồn) bên dưới.

---

## Mục lục

- [Bản quyền font nguồn](#bản-quyền-font-nguồn)
- [Tính năng](#tính-năng)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Cài đặt](#cài-đặt)
- [Cách dùng](#cách-dùng)
- [Đặc điểm kỹ thuật](#đặc-điểm-kỹ-thuật)
- [Giới hạn đã biết](#giới-hạn-đã-biết)
- [Tạo lại font từ TTF khác](#tạo-lại-font-từ-ttf-khác)
- [Gỡ lỗi thường gặp](#gỡ-lỗi-thường-gặp)

---

## Bản quyền font nguồn

File nguồn `tools/FVF Fernando 08.ttf` có metadata:

```
Copyright © Font Viet 2004. All rights reserved.
Designed and encoded by Nguyễn Hùng Trà - www.fontviet.com
```

## Tính năng

- **Tiếng Việt đầy đủ dấu** — font nguồn có sẵn toàn bộ glyph tiếng Việt
  (xác nhận qua `fontTools`), tự giải mã UTF-8 nội bộ.
- **3 kiểu định dạng, kết hợp tự do**: thường, đậm (faux-bold), nghiêng
  (faux-italic, cắt xiên lúc vẽ), gạch chân — qua bitmask.
- **Bề rộng theo tỷ lệ** (proportional) — mỗi ký tự có độ rộng riêng,
  không cố định như font monospace.
- **Tối ưu bộ nhớ** — mỗi ký tự chỉ lưu đúng số hàng có nét thực tế
  (không lưu hàng trắng thừa), giảm ~51% dung lượng so với lưu cố định.
- **Độc lập driver** — chỉ cần `u8g2.drawPixel(x, y)`, không đụng vào
  font engine/`.setFont()` của U8g2, nên dùng được với driver màn hình
  tự viết bất kỳ (xem `ST75256_Custom_Driver` trong repo `vcode`).

## Cấu trúc thư mục

```
FVF_Fernando_Font/
  README.md                    <- file nay
  font_fvf_fernando.h           <- font thuong (fvfDrawString)
  font_fvf_fernando_bold.h      <- font dam / faux-bold (fvfBDrawString)
  font_fvf_fernando_style.h     <- lop hop nhat: dam/nghieng/gach chan
                                    ket hop tu do (fvfDrawStringStyled)
  tools/
    FVF Fernando 08.ttf         <- font nguon (CO BAN QUYEN, xem tren)
    gen_fvf_font.py              <- script Python sinh lai 2 file .h
    audit_font.py                <- script kiem tra chat luong glyph
```

## Cài đặt

### Yêu cầu

- Arduino IDE (hoặc PlatformIO) đã cấu hình build cho board ESP32/STM32
  đang dùng.
- Một driver màn hình có method `drawPixel(int x, int y)` khả dụng qua
  đối tượng kiểu `U8G2&` — ví dụ `ST75256_Custom_Driver` sẵn có trong
  cùng dự án (`vcode/vcode/`, `vcode/ST75256_Custom_Driver/`), hoặc bất
  kỳ class con nào của `U8G2` trong thư viện U8g2 gốc.
- (Chỉ cần nếu muốn **tạo lại** font, không cần để **dùng** font có sẵn)
  Python 3 + `pip install pillow`, và `pip install fonttools` nếu muốn
  tự kiểm tra glyph coverage.

### Bước cài đặt (dùng font có sẵn, không cần Python)

1. Copy 3 file `.h` ở thư mục gốc (`font_fvf_fernando.h`,
   `font_fvf_fernando_bold.h`, `font_fvf_fernando_style.h`) — **không cần
   thư mục `tools/`** — vào **cùng thư mục** với file `.ino` chính của
   sketch. Arduino IDE tự động biên dịch mọi `.h`/`.c`/`.cpp` nằm cùng
   thư mục với sketch, không cần cài vào `Documents/Arduino/libraries/`.
2. Copy thêm các file driver màn hình (`U8g2_ST75256_Custom.h`,
   `st75256_custom_config.h`, `u8x8_d_st75256_custom.h/.c`,
   `u8g2_setup_st75256_custom.c` — xem repo `ST75256_Custom_Driver`) vào
   chung thư mục đó nếu chưa có.
3. Trong sketch, include theo đúng thứ tự (style phụ thuộc cả 2 file kia):

   ```cpp
   #include <U8g2lib.h>
   #include "U8g2_ST75256_Custom.h"   // hoac driver man hinh khac cua ban

   #include "font_fvf_fernando.h"
   #include "font_fvf_fernando_bold.h"
   #include "font_fvf_fernando_style.h"
   ```

4. Build và nạp như bình thường.

## Cách dùng

```cpp
u8g2.setDrawColor(1);   // bat buoc truoc khi goi ham ve font nay

// Thuong
fvfDrawString(u8g2, 5, 5, "Xin chào Việt Nam");

// Dam (faux-bold)
fvfBDrawString(u8g2, 5, 25, "Đậm");

// Nghieng (faux-italic, cat xien luc ve)
fvfDrawStringStyled(u8g2, 5, 45, "Nghiêng", FVF_ITALIC);

// Ket hop dam + gach chan
fvfDrawStringStyled(u8g2, 5, 65, "Đậm gạch chân", FVF_BOLD | FVF_UNDERLINE);
```

**Lưu ý toạ độ:** `y` truyền vào là **đỉnh của khung dòng chung**, không
phải đỉnh riêng của từng ký tự (mỗi ký tự tự vẽ lùi xuống đúng vị trí nhờ
`yOffset` lưu sẵn, để dấu tiếng Việt + chữ có đuôi như `g, y, p` thẳng
hàng đúng baseline). Mỗi dòng nên cách nhau tối thiểu `FVF_LINE_ROWS`
(hằng số định nghĩa trong `font_fvf_fernando_style.h`, hiện = 18) pixel.

Các bitmask trong `font_fvf_fernando_style.h`:

| Hằng số          | Ý nghĩa                          |
|------------------|-----------------------------------|
| `FVF_NORMAL`     | Không định dạng gì (mặc định)     |
| `FVF_BOLD`       | Đậm (dùng bảng glyph faux-bold)   |
| `FVF_ITALIC`     | Nghiêng (cắt xiên lúc vẽ)         |
| `FVF_UNDERLINE`  | Gạch chân (vẽ thêm 1 đường ngang) |

Kết hợp bằng toán tử `|`, ví dụ `FVF_BOLD | FVF_ITALIC | FVF_UNDERLINE`.

Demo đầy đủ: xem `vcode/FVFFontDemo/FVFFontDemo.ino` trong repo.

## Đặc điểm kỹ thuật

- **Cỡ render nguồn**: 8px (đo từ font TTF), cắt theo vùng mực chung của
  toàn bộ 229 ký tự (ASCII + tiếng Việt) → khung dòng cao 18 hàng. Đã thử
  cỡ nhỏ hơn (5-6px) nhưng chữ tròn (a, e, o) bị rút thành khối đặc, mất
  hết phần bụng chữ, và dấu thanh tiếng Việt (sắc/ngã/hỏi) không phân
  biệt được — 8px là điểm cân bằng giữ được cả hình chữ lẫn dấu.
- **Đóng gói bộ nhớ**: mỗi ký tự lưu `(yOffset, height, dataIndex)` trỏ
  vào 1 mảng dữ liệu hàng dùng chung, chỉ lưu đúng số hàng có nét — giảm
  ~51% so với lưu cố định 18 hàng cho mọi ký tự.
- **Định dạng hàng**: `uint16_t`/hàng (tối đa 16 cột) — bắt buộc vì `m`,
  `M`, `W` thực tế rộng tới 10-12px ở cỡ render 8px; dùng `uint8_t` (8
  cột) sẽ cắt cụt các ký tự này.
- **Tiếng Việt**: dựng bảng ký tự bằng tổ hợp NFC (nguyên âm nền +
  combining mark dấu thanh) trong `gen_fvf_font.py`, rồi kiểm tra font
  nguồn có glyph tương ứng không qua Pillow. Vẽ chuỗi phải qua
  `fvfUtf8Decode()` nội bộ (font này không tương thích
  `u8g2.drawStr()`/`drawUTF8()` vì không phải font của U8g2).
- **Đậm**: faux-bold — chồng bản thân dịch phải 1px lúc SINH font (không
  phải style Bold thật của nhà thiết kế, vì font nguồn không có).
- **Nghiêng**: faux-italic — cắt xiên (shear) lúc VẼ (không nằm trong dữ
  liệu font): hàng càng gần đỉnh dòng dịch phải càng nhiều, hàng gần đáy
  dịch ít/không dịch.

## Giới hạn đã biết

- **`I` hoa và `l` thường render giống hệt nhau.** Đã xác nhận đây là do
  chính **font gốc thiết kế giống nhau** (kiểm tra ở cỡ lớn 20px, cả 2
  đều chỉ là 1 nét thẳng đứng không serif/chấm), không phải lỗi trích
  xuất — không sửa được nếu không thêm chi tiết KHÔNG có trong font gốc.
- Dấu thanh tiếng Việt (sắc/ngã/hỏi) phân biệt được nhưng khá tinh tế ở
  kích thước màn thật nhỏ — đã đánh đổi kích thước dòng lớn hơn Unifont
  có sẵn của U8g2 (18px so với 16px) để đổi lấy việc phân biệt được rõ.
- Nghiêng chỉ là hiệu ứng cắt xiên đơn giản lúc vẽ, không phải nét
  nghiêng thật do nhà thiết kế font vẽ riêng (font nguồn không có style
  Italic).
- Không hỗ trợ font engine `.setFont()`/`.drawStr()` chuẩn của U8g2 — bắt
  buộc dùng các hàm `fvf...` riêng của font này.

## Tạo lại font từ TTF khác

Nếu muốn đổi sang font khác (khuyến nghị nếu định public hoá dự án - chọn
font có giấy phép mở như SIL OFL):

1. Cài Python 3, `pip install pillow fonttools`.
2. Copy file `.ttf` mới vào `tools/`, sửa dòng
   `ImageFont.truetype('TEN_FONT.ttf', SIZE)` trong `gen_fvf_font.py`.
3. (Tuỳ chọn) Chỉnh `SIZE` (cỡ render, hiện = 8) và ngưỡng nhị phân hoá
   (`if px > 100:` trong hàm `glyph_bits()`) nếu chữ ra quá đậm/quá nhạt.
4. Chạy:

   ```
   cd tools
   python gen_fvf_font.py
   ```

   Script tự đo lại vùng mực chung (`ROW_TOP`, `ROWS`) và ghi đè 2 file
   `../font_fvf_fernando.h` + `../font_fvf_fernando_bold.h`.
5. Chạy `python audit_font.py` để kiểm tra: ký tự mất nét, 2 ký tự khác
   nhau bị trùng bitmap, bề rộng bất thường.

## Gỡ lỗi thường gặp

| Triệu chứng | Nguyên nhân / cách sửa |
|---|---|
| Chữ tiếng Việt ra ô vuông/trắng | Dùng nhầm `u8g2.drawStr()` thay vì `fvfDrawString()` — font này không qua engine của U8g2. |
| Chữ rộng (`m`, `M`, `W`) bị cắt cụt bên phải | Đã sửa ở bản hiện tại (chuyển sang `uint16_t`/hàng). Nếu tự tạo lại font khác và gặp lại, tăng `min(width, 16)` trong `glyph_bits()`. |
| Dấu mũ (^) nhìn như 2 chấm rời | Do render font ở cỡ quá nhỏ. Tăng `SIZE` trong `gen_fvf_font.py` rồi tạo lại (đánh đổi: dòng cao hơn). |
| Build lỗi "redefinition" khi dùng cả 3 file `.h` | Kiểm tra chỉ include các file 1 lần, đúng thứ tự (`font_fvf_fernando.h` và `_bold.h` PHẢI có trước `_style.h`). |
| Nạp lên board nhưng không thấy chữ nào | Kiểm tra đã gọi `u8g2.setDrawColor(1)` trước khi gọi hàm `fvf...`, và đã `u8g2.sendBuffer()` sau khi vẽ. |
