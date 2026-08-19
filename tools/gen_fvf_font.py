import unicodedata
from PIL import Image, ImageDraw, ImageFont

SIZE = 8       # size=6: dau ngang/sac/nga/hoi chi con 1-2 pixel, kho phan biet (nga
               # trong giong sac). size=8: dau co ~2-3 hang rieng, phan biet duoc ro
               # hon (sac=1 net cheo, nga=2 diem tach roi, hoi=net cheo dai hon) -
               # van con kha subtle o kich thuoc man that, khong the hoan hao 100%
               # neu khong lam font to hon nua (mat y nghia "mini").
ORIGIN_X = 4   # left padding to safely capture negative left-bearings
CANVAS = 32

f = ImageFont.truetype('FVF Fernando 08.ttf', SIZE)   # file nay nam cung thu muc tools/

# --- Sinh danh sach ky tu tieng Viet bang to hop dau am NFC ---
BASE_VOWELS = ['a', 'ă', 'â', 'e', 'ê', 'i', 'o', 'ô', 'ơ', 'u', 'ư', 'y']
TONE_MARKS = ['', '̀', '́', '̉', '̃', '̣']  # ngang,huyen,sac,hoi,nga,nang

viet_chars = []
for base in BASE_VOWELS:
    for case in (base, base.upper()):
        for tone in TONE_MARKS:
            composed = unicodedata.normalize('NFC', case + tone)
            if len(composed) == 1 and composed not in viet_chars:
                viet_chars.append(composed)
for extra in ['đ', 'Đ']:
    viet_chars.append(extra)

ascii_chars = [chr(c) for c in range(0x20, 0x7F)]
ALL_CHARS = ascii_chars + [c for c in viet_chars if c not in ascii_chars]


def measure_window():
    """Do vung muc (ink) chung cua TOAN BO ky tu (ASCII + Viet) de xac dinh
    dong bao nhieu pixel can thiet - lam moi lan doi SIZE/font de tranh cat
    mat dau/duoi chu (bug da gap khi hardcode gia tri cu cho ASCII-only)."""
    min_top, max_bottom = 999, -999
    for ch in ALL_CHARS:
        if ch == ' ':
            continue
        img = Image.new('L', (CANVAS, CANVAS), 0)
        d = ImageDraw.Draw(img)
        d.text((ORIGIN_X, 5), ch, font=f, fill=255)
        bbox = img.getbbox()
        if bbox:
            min_top = min(min_top, bbox[1])
            max_bottom = max(max_bottom, bbox[3])
    return min_top, max_bottom - min_top


ROW_TOP, ROWS = measure_window()
print('Do duoc vung muc: ROW_TOP=%d ROWS=%d' % (ROW_TOP, ROWS))


def glyph_bits(ch, bold):
    img = Image.new('L', (CANVAS, CANVAS), 0)
    d = ImageDraw.Draw(img)
    d.text((ORIGIN_X, 5), ch, font=f, fill=255)
    bbox = img.getbbox()
    if bbox is None:
        return 2, [0] * ROWS
    left, top, right, bottom = bbox
    left = min(left, ORIGIN_X)
    width = max(1, right - left)
    # LUU Y: da tung gioi han width<=8 (vua 1 byte/hang) va lam CAT CUT chu
    # 'm','M','W','@' (thuc te can toi 12px o SIZE=8) - gio dung uint16_t/
    # hang (toi da 16 cot) de khong con mat net chu rong.
    width = min(width, 16)
    rows = []
    for ry in range(ROW_TOP, ROW_TOP + ROWS):
        b = 0
        for cx in range(width):
            px = img.getpixel((left + cx, ry)) if (left + cx) < CANVAS and ry < CANVAS else 0
            if px > 100:
                b |= (0x8000 >> cx)
        rows.append(b)
    if bold:
        # Faux-bold: chong them 1px dich phai len chinh no (ky thuat chuan
        # khi khong co ban Bold that cua font). Tang width them 1 (neu con
        # cho, toi da 16 bit) de khong bi cat mat phan tran ra ben phai.
        rows = [r | (r >> 1) for r in rows]
        if width < 16:
            width += 1
    return width, rows


def trim_glyph(rows):
    """Cat bot hang trang thua o dau/cuoi tung glyph (tiet kiem bo nho): chi
    luu tu hang co muc dau tien den hang co muc cuoi cung, kem yOffset de
    biet ve lui xuong bao nhieu so voi dinh khung dong chung."""
    first = next((i for i, r in enumerate(rows) if r != 0), None)
    if first is None:
        return 0, 0, []
    last = max(i for i, r in enumerate(rows) if r != 0)
    return first, last - first + 1, rows[first:last + 1]


def generate(bold):
    suffix = 'B' if bold else ''
    filename = 'font_fvf_fernando_bold.h' if bold else 'font_fvf_fernando.h'
    out_path = '../' + filename   # script nam trong tools/, file .h xuat ra thu muc cha
    style_name = 'dam (faux-bold)' if bold else 'thuong'

    glyphs = []
    for ch in ALL_CHARS:
        cp = ord(ch)
        if ch == ' ':
            width, full_rows = 3, [0] * ROWS
        else:
            width, full_rows = glyph_bits(ch, bold)
        y_off, height, trimmed = trim_glyph(full_rows)
        glyphs.append((cp, ch, width, y_off, height, trimmed))

    rowdata = []
    entries = []
    for cp, ch, width, y_off, height, trimmed in glyphs:
        data_index = len(rowdata)
        rowdata.extend(trimmed)
        entries.append((cp, ch, width, y_off, height, data_index))

    # 1 hang = 2 byte (uint16_t, ho tro toi 16 cot - can thiet vi 'm','M','W'
    # thuc te rong toi 10-12px, uint8_t cu (8 cot) da lam CAT CUT cac chu nay).
    bytes_uncropped = len(ALL_CHARS) * ROWS * 2
    bytes_actual = len(rowdata) * 2
    print('[%s] Bo nho ROWDATA: %d byte (neu khong cat trang) -> %d byte (da cat), giam %.0f%%' %
          (style_name, bytes_uncropped, bytes_actual, 100 * (1 - bytes_actual / bytes_uncropped)))

    lines = []
    lines.append('/*')
    lines.append('  %s' % filename)
    lines.append('')
    lines.append('  Font bitmap %s tu dong trich xuat tu "FVF Fernando 08.ttf" (font vector,' % style_name)
    lines.append('  KHONG phai bitmap strike co san - da render + threshold nhi phan bang')
    lines.append('  Python/PIL o kich thuoc %dpx. Khung dong chung cao %d hang, nhung tung' % (SIZE, ROWS))
    lines.append('  ky tu chi luu dung so hang co muc thuc te (yOffset + height) - khong')
    lines.append('  luu thua hang trang, tiet kiem bo nho dang ke so voi luu co dinh %d hang.' % ROWS)
    lines.append('  Font co chieu rong PROPORTIONAL (moi ky tu 1 do rong rieng).')
    if bold:
        lines.append('')
        lines.append('  BAN DAM: font goc KHONG co style Bold rieng, day la "faux-bold" tu')
        lines.append('  tong hop (chong 1px dich phai len chinh glyph thuong) - khong phai')
        lines.append('  net ve chuan cua nha thiet ke, chi la mo phong do dam hon.')
    lines.append('')
    lines.append('  DA XAC NHAN qua fontTools: font nguon co DAY DU glyph tieng Viet (ca')
    lines.append('  52 ky tu dac trung + cac to hop dau am co ban), nen font nay ho tro')
    lines.append('  tieng Viet co dau day du.')
    lines.append('')
    lines.append('  Dung u8g2.drawPixel() truc tiep, KHONG qua font engine cua U8g2. Vi')
    lines.append('  chuoi tieng Viet la UTF-8 nhieu byte/ky tu, PHAI dung fvf%sDrawString()' % suffix)
    lines.append('  (tu giai ma UTF-8 ben trong), KHONG dung drawStr()/drawUTF8() cua u8g2.')
    lines.append('')
    lines.append('  Cach dung trong sketch:')
    lines.append('    #include "%s"' % filename)
    lines.append('    ...')
    lines.append('    u8g2.setDrawColor(1);')
    lines.append('    fvf%sDrawString(u8g2, 5, 10, "Xin chào");' % suffix)
    lines.append('')
    lines.append('  Muon tao lai (doi kich thuoc/threshold/font khac): sua gen_fvf_font.py')
    lines.append('  (can Python 3 + Pillow: pip install pillow) roi chay lai, se ghi de')
    lines.append('  file nay.')
    lines.append('*/')
    lines.append('')
    lines.append('#pragma once')
    lines.append('#include <U8g2lib.h>')
    lines.append('')
    lines.append('typedef struct { uint32_t cp; uint8_t width; uint8_t yOffset; uint8_t height; uint16_t dataIndex; } FVF%sGlyph;' % suffix)
    lines.append('')
    lines.append('static const uint16_t FVF%s_ROWDATA[%d] = {' % (suffix, max(1, len(rowdata))))
    for i in range(0, len(rowdata), 12):
        chunk = rowdata[i:i + 12]
        lines.append('  ' + ', '.join('0x%04X' % b for b in chunk) + ',')
    lines.append('};')
    lines.append('')
    lines.append('static const FVF%sGlyph FVF%s_FONT[%d] = {' % (suffix, suffix, len(entries)))
    for cp, ch, width, y_off, height, data_index in entries:
        label = ch if (0x20 <= cp <= 0x7E and ch not in "'\\") else '?'
        lines.append('  /* %s U+%04X */ { 0x%04X, %d, %d, %d, %d },' %
                      (label, cp, cp, width, y_off, height, data_index))
    lines.append('};')
    lines.append('#define FVF%s_FONT_COUNT %d' % (suffix, len(entries)))
    lines.append('')
    lines.append('static const FVF%sGlyph *fvf%sFindGlyph(uint32_t cp)' % (suffix, suffix))
    lines.append('{')
    lines.append('  for (uint16_t i = 0; i < FVF%s_FONT_COUNT; i++) {' % suffix)
    lines.append('    if (FVF%s_FONT[i].cp == cp) return &FVF%s_FONT[i];' % (suffix, suffix))
    lines.append('  }')
    lines.append('  return &FVF%s_FONT[0];   // khong tim thay -> khoang trang' % suffix)
    lines.append('}')
    lines.append('')
    lines.append('// Giai ma 1 ky tu UTF-8 tai vi tri p, tra ve codepoint va tu dong day p toi')
    lines.append('// ky tu tiep theo.')
    lines.append('static uint32_t fvf%sUtf8Decode(const char *&p)' % suffix)
    lines.append('{')
    lines.append('  uint8_t c = (uint8_t)*p++;')
    lines.append('  if (c < 0x80) return c;')
    lines.append('  if ((c & 0xE0) == 0xC0) {')
    lines.append('    uint32_t cp = c & 0x1F;')
    lines.append('    cp = (cp << 6) | (uint8_t)(*p++ & 0x3F);')
    lines.append('    return cp;')
    lines.append('  }')
    lines.append('  if ((c & 0xF0) == 0xE0) {')
    lines.append('    uint32_t cp = c & 0x0F;')
    lines.append('    cp = (cp << 6) | (uint8_t)(*p++ & 0x3F);')
    lines.append('    cp = (cp << 6) | (uint8_t)(*p++ & 0x3F);')
    lines.append('    return cp;')
    lines.append('  }')
    lines.append('  if ((c & 0xF8) == 0xF0) {')
    lines.append('    uint32_t cp = c & 0x07;')
    lines.append('    cp = (cp << 6) | (uint8_t)(*p++ & 0x3F);')
    lines.append('    cp = (cp << 6) | (uint8_t)(*p++ & 0x3F);')
    lines.append('    cp = (cp << 6) | (uint8_t)(*p++ & 0x3F);')
    lines.append('    return cp;')
    lines.append('  }')
    lines.append('  return c;')
    lines.append('}')
    lines.append('')
    lines.append('// Ve 1 ky tu (theo Unicode codepoint) bang font FVF Fernando %s. u8g2 phai' % style_name)
    lines.append('// duoc setDrawColor() truoc. y la dinh khung dong chung (KHONG phai dinh')
    lines.append('// ky tu) - glyph tu ve lui xuong dung yOffset da luu san.')
    lines.append('static void fvf%sDrawChar(U8G2 &u8g2, int x, int y, uint32_t cp)' % suffix)
    lines.append('{')
    lines.append('  const FVF%sGlyph *g = fvf%sFindGlyph(cp);' % (suffix, suffix))
    lines.append('  for (int row = 0; row < g->height; row++) {')
    lines.append('    uint16_t bits = FVF%s_ROWDATA[g->dataIndex + row];' % suffix)
    lines.append('    for (int col = 0; col < g->width; col++) {')
    lines.append('      if (bits & (0x8000 >> col))')
    lines.append('        u8g2.drawPixel(x + col, y + g->yOffset + row);')
    lines.append('    }')
    lines.append('  }')
    lines.append('}')
    lines.append('')
    lines.append('// Ve chuoi UTF-8 (co the co dau tieng Viet) bang font FVF Fernando %s, tra' % style_name)
    lines.append('// ve tong be rong da ve.')
    lines.append('static int fvf%sDrawString(U8G2 &u8g2, int x, int y, const char *utf8)' % suffix)
    lines.append('{')
    lines.append('  int cx = x;')
    lines.append('  const char *p = utf8;')
    lines.append('  while (*p) {')
    lines.append('    uint32_t cp = fvf%sUtf8Decode(p);' % suffix)
    lines.append('    const FVF%sGlyph *g = fvf%sFindGlyph(cp);' % (suffix, suffix))
    lines.append('    fvf%sDrawChar(u8g2, cx, y, cp);' % suffix)
    lines.append('    cx += g->width + 1;')
    lines.append('  }')
    lines.append('  return cx - x;')
    lines.append('}')
    lines.append('')

    with open(out_path, 'w', encoding='utf-8') as fp:
        fp.write('\n'.join(lines) + '\n')

    print('Da tao %s, %d dong, %d ky tu' % (out_path, len(lines), len(ALL_CHARS)))


generate(bold=False)
generate(bold=True)
