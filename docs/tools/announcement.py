#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Домовед · генератор ежемесячного объявления по спецсчёту.

Рисует картинку в том же виде, в каком объявления делались раньше:
тёмно-бирюзовая шапка, период, оплачено собственниками, начислено
процентов, остаток на счёте.

Использование из командной строки:

    python3 announcement.py \
        --period 2026-06 \
        --paid 71661.16 \
        --interest 8253.70 \
        --balance 2051123.18 \
        --balance-date 2026-06-30 \
        --out iyun-2026.png

Использование из бота:

    from announcement import render
    path = render(period="2026-07", paid=..., interest=...,
                  balance=..., balance_date="2026-07-31",
                  out="iyul-2026.png")

Требуется Pillow: pip install pillow
"""

import argparse
import os

from PIL import Image, ImageDraw, ImageFont

# ── фирменные цвета (сняты с исходного объявления) ──────────
HEAD_BG = (14, 118, 109)     # #0E766D  шапка
SUB_BG = (109, 172, 181)     # #6DACB5  полоса подзаголовка
PAGE_BG = (183, 197, 198)    # #B7C5C6  фон
TILE_TQ = (158, 195, 187)    # #9EC3BB  бирюзовая плашка
TILE_GREY = (198, 197, 203)  # #C6C5CB  серая плашка
INK = (11, 77, 71)           # #0B4D47  тёмно-бирюзовый текст
INK_SOFT = (23, 92, 85)
WHITE = (255, 255, 255)

# ── размеры холста ──────────────────────────────────────────
W, H = 1180, 810             # пропорции исходника, крупнее для чёткости
PAD = 56                     # поля

MONTHS_GEN = ['ЯНВАРЬ', 'ФЕВРАЛЬ', 'МАРТ', 'АПРЕЛЬ', 'МАЙ', 'ИЮНЬ',
              'ИЮЛЬ', 'АВГУСТ', 'СЕНТЯБРЬ', 'ОКТЯБРЬ', 'НОЯБРЬ', 'ДЕКАБРЬ']

FONT_DIRS = [
    '/usr/share/fonts/truetype/dejavu/',
    '/usr/share/fonts/dejavu/',
    '/Library/Fonts/',
    'C:/Windows/Fonts/',
]


def _font(name, size):
    """Ищет шрифт в типичных местах, иначе берёт шрифт по умолчанию."""
    for d in FONT_DIRS:
        path = os.path.join(d, name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def money(value):
    """71661.16 → '71 661,16 ₽'"""
    if value is None:
        return '—'
    n = float(value)
    whole = int(abs(n))
    cents = int(round((abs(n) - whole) * 100))
    s = f'{whole:,}'.replace(',', ' ')
    return f'{s},{cents:02d} ₽' if n >= 0 else f'−{s},{cents:02d} ₽'


def period_title(period):
    """'2026-06' → 'за ИЮНЬ 2026 г'"""
    year, month = period.split('-')
    return f'за {MONTHS_GEN[int(month) - 1]} {year} г'


def date_ru(value):
    """'2026-06-30' → '30.06.2026'"""
    y, m, d = value.split('-')
    return f'{d}.{m}.{y}'


def _centered(draw, text, font, fill, cx, y):
    w = draw.textlength(text, font=font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def render(period, paid, interest, balance, balance_date,
           address='Магистральная, 2', out='announcement.png'):
    """Рисует объявление и сохраняет в файл. Возвращает путь к файлу."""
    img = Image.new('RGB', (W, H), PAGE_BG)
    d = ImageDraw.Draw(img)

    f_head = _font('DejaVuSans-Bold.ttf', 46)
    f_sub = _font('DejaVuSans-Bold.ttf', 23)
    f_period = _font('DejaVuSans-Bold.ttf', 50)
    f_lab = _font('DejaVuSans-Bold.ttf', 27)
    f_val = _font('DejaVuSans-Bold.ttf', 44)
    f_lab_big = _font('DejaVuSans-Bold.ttf', 29)
    f_val_big = _font('DejaVuSans-Bold.ttf', 60)

    cx = W / 2

    # шапка
    d.rectangle([0, 0, W, 92], fill=HEAD_BG)
    _centered(d, 'ВЗНОСЫ НА КАПИТАЛЬНЫЙ РЕМОНТ', f_head, WHITE, cx, 22)

    # полоса подзаголовка
    d.rectangle([0, 92, W, 145], fill=SUB_BG)
    _centered(d, f'Спецсчёт МКД {address} · ежемесячная информация для собственников',
              f_sub, (7, 51, 47), cx, 105)

    # период
    d.rectangle([PAD, 190, W - PAD, 288], fill=TILE_TQ)
    _centered(d, period_title(period), f_period, INK, cx, 212)

    # два показателя
    top, bottom = 326, 500
    mid = W / 2
    d.rectangle([PAD, top, W - PAD, bottom], fill=TILE_GREY)

    left_cx = PAD + (mid - PAD) / 2
    right_cx = mid + (W - PAD - mid) / 2

    _centered(d, 'ОПЛАЧЕНО СОБСТВЕННИКАМИ', f_lab, INK_SOFT, left_cx, top + 24)
    _centered(d, 'ЗА ЭТОТ МЕСЯЦ', f_lab, INK_SOFT, left_cx, top + 58)
    _centered(d, money(paid), f_val, INK, left_cx, top + 108)

    _centered(d, 'НАЧИСЛЕНО ПРОЦЕНТОВ', f_lab, INK_SOFT, right_cx, top + 24)
    _centered(d, 'ПО СПЕЦСЧЁТУ', f_lab, INK_SOFT, right_cx, top + 58)
    _centered(d, money(interest), f_val, INK, right_cx, top + 108)

    # остаток
    d.rectangle([PAD, 542, W - PAD, 748], fill=TILE_TQ)
    _centered(d, f'ОСТАТОК ОБЩЕЙ СУММЫ НА СЧЁТЕ на {date_ru(balance_date)}',
              f_lab_big, INK, cx, 578)
    _centered(d, money(balance), f_val_big, INK, cx, 646)

    img.save(out, optimize=True)
    return out


def main():
    p = argparse.ArgumentParser(description='Объявление по спецсчёту капремонта')
    p.add_argument('--period', required=True, help='месяц данных, например 2026-06')
    p.add_argument('--paid', type=float, required=True, help='оплачено собственниками')
    p.add_argument('--interest', type=float, required=True, help='начислено процентов')
    p.add_argument('--balance', type=float, required=True, help='остаток на счёте')
    p.add_argument('--balance-date', required=True, help='дата остатка, например 2026-06-30')
    p.add_argument('--address', default='Магистральная, 2')
    p.add_argument('--out', default='announcement.png')
    a = p.parse_args()

    path = render(a.period, a.paid, a.interest, a.balance,
                  a.balance_date, a.address, a.out)
    print(path)


if __name__ == '__main__':
    main()
