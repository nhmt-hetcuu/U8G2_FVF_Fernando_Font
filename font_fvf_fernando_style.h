/*
  font_fvf_fernando_style.h

  Lop dinh dang hop nhat cho font_fvf_fernando.h / font_fvf_fernando_bold.h -
  cho phep ket hop DAM + NGHIENG + GACH CHAN tuy y (bitmask), thay vi phai
  goi rieng tung ham cho tung kieu.

  PHAI include CA HAI file font_fvf_fernando.h VA font_fvf_fernando_bold.h
  TRUOC file nay:

    #include "font_fvf_fernando.h"
    #include "font_fvf_fernando_bold.h"
    #include "font_fvf_fernando_style.h"
    ...
    fvfDrawStringStyled(u8g2, x, y, "Xin chào", FVF_BOLD | FVF_UNDERLINE);
    fvfDrawStringStyled(u8g2, x, y, "Xin chào", FVF_ITALIC);

  Cach lam:
    - DAM: dung lai bang glyph "bold" da tao san trong font_fvf_fernando_bold.h
      (faux-bold: chong 1px dich phai len glyph thuong luc SINH FONT).
    - NGHIENG: mo phong bang CAT XIEN (shear) LUC VE - hang cang gan dinh
      dong (tren cung) cang dich sang phai nhieu hon hang gan day dong,
      tao cam giac nghieng ma khong can du lieu font rieng.
    - GACH CHAN: ve 1 duong ngang ngay duoi dong chu sau khi ve xong.

  FVF_LINE_ROWS PHAI khop voi ROWS luc chay gen_fvf_font.py (in ra khi
  chay script, hien tai la 18) - neu sau nay doi SIZE cua font va sinh
  lai, nho cap nhat lai hang so nay cho dung do nghieng.
*/

#pragma once
#include "font_fvf_fernando.h"
#include "font_fvf_fernando_bold.h"

#define FVF_NORMAL     0x00
#define FVF_BOLD       0x01
#define FVF_ITALIC     0x02
#define FVF_UNDERLINE  0x04

#define FVF_LINE_ROWS  18   // xem ghi chu tren dau file - phai khop ROWS thuc te

// Ve 1 ky tu voi style tuy chinh. Tra ve be rong da ve (de tinh con tro).
static uint8_t fvfDrawCharStyled(U8G2 &u8g2, int x, int y, uint32_t cp, uint8_t style)
{
  uint8_t width, yOffset, height;
  uint16_t dataIndex;
  const uint16_t *pool;

  if (style & FVF_BOLD) {
    const FVFBGlyph *g = fvfBFindGlyph(cp);
    width = g->width; yOffset = g->yOffset; height = g->height;
    dataIndex = g->dataIndex; pool = FVFB_ROWDATA;
  } else {
    const FVFGlyph *g = fvfFindGlyph(cp);
    width = g->width; yOffset = g->yOffset; height = g->height;
    dataIndex = g->dataIndex; pool = FVF_ROWDATA;
  }

  for (int row = 0; row < height; row++) {
    uint16_t bits = pool[dataIndex + row];
    int absRow = yOffset + row;
    // Cang gan dinh dong (absRow nho) cang dich phai nhieu -> nghieng ve phai
    int shear = (style & FVF_ITALIC) ? (FVF_LINE_ROWS - 1 - absRow) / 4 : 0;
    for (int col = 0; col < width; col++) {
      if (bits & (0x8000 >> col))
        u8g2.drawPixel(x + col + shear, y + absRow);
    }
  }
  return width;
}

// Ve chuoi UTF-8 voi style tuy chinh (ket hop bitmask FVF_BOLD|FVF_ITALIC|
// FVF_UNDERLINE). Tra ve tong be rong da ve.
static int fvfDrawStringStyled(U8G2 &u8g2, int x, int y, const char *utf8, uint8_t style)
{
  int cx = x;
  const char *p = utf8;
  int maxShear = (style & FVF_ITALIC) ? (FVF_LINE_ROWS - 1) / 4 : 0;

  while (*p) {
    uint32_t cp = fvfUtf8Decode(p);   // giai ma UTF-8 giong nhau cho ca 2 font
    uint8_t width = fvfDrawCharStyled(u8g2, cx, y, cp, style);
    cx += width + 1 + (maxShear > 0 ? 1 : 0);   // them chut khoang cach neu nghieng, tranh de chu
  }

  if (style & FVF_UNDERLINE) {
    u8g2.drawHLine(x, y + FVF_LINE_ROWS, cx - x - 1);
  }

  return cx - x;
}
