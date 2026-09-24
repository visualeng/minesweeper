# -*- coding: utf-8 -*-
# генератор тайлов сапера: рисуем сами, ничего не скачиваем.
#
# вид классический, как в виндовс-сапере: серые плитки с фаской, обычные
# цветные цифры. градиентов, шума, глянца и неона тут нет специально -
# одна заливка, как и было в оригинале.
#
# запуск: python build_tiles.py

import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "tiles")

SIZE = 48        # итоговый тайл
SS = 4           # круги и линии рисуем в 4 раза крупнее, потом уменьшаем
GLYPH_H = 32     # высота цифры
BEVEL = 5        # толщина фаски закрытой клетки
LINE = 3         # толщина линии сетки на раскрытой клетке

FACE = (192, 192, 192)   # c0c0c0 - тот же серый, что и в оригинале
HILITE = (255, 255, 255)
SHADOW = (128, 128, 128)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# цифры по-старому: у каждой свой цвет, ничего яркого
DIGIT_COLORS = {
    1: (0, 0, 255),
    2: (0, 128, 0),
    3: (255, 0, 0),
    4: (0, 0, 128),
    5: (128, 0, 0),
    6: (0, 128, 128),
    7: (0, 0, 0),
    8: (128, 128, 128),
}


def smooth(draw_it):
    """рисуем в SS раз крупнее и уменьшаем - круги и линии не рвутся"""
    im = Image.new("RGBA", (SIZE * SS, SIZE * SS), (0, 0, 0, 0))
    draw_it(ImageDraw.Draw(im), SS)
    return im.resize((SIZE, SIZE), Image.LANCZOS)


def over(base, sprite):
    """кладём спрайт поверх плитки"""
    b = base.convert("RGBA")
    b.alpha_composite(sprite)
    return b.convert("RGB")


def closed():
    """закрытая клетка: серый квадрат с фаской - белая сверху/слева,
    тёмная снизу/справа. читается выпуклой, как в оригинале"""
    im = Image.new("RGB", (SIZE, SIZE), FACE)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, SIZE - 1, BEVEL - 1], fill=HILITE)          # верх
    d.rectangle([0, 0, BEVEL - 1, SIZE - 1], fill=HILITE)          # лево
    d.rectangle([0, SIZE - BEVEL, SIZE - 1, SIZE - 1], fill=SHADOW)  # низ
    d.rectangle([SIZE - BEVEL, 0, SIZE - 1, SIZE - 1], fill=SHADOW)  # право
    return im


def opened():
    """раскрытая клетка: та же заливка без фаски + линии сетки сверху и слева,
    из них собирается вся решётка открытого поля"""
    im = Image.new("RGB", (SIZE, SIZE), FACE)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, SIZE - 1, LINE - 1], fill=SHADOW)
    d.rectangle([0, 0, LINE - 1, SIZE - 1], fill=SHADOW)
    return im


def font_for_height(txt, target):
    """подбираем кегль по высоте знака - цифры будут одного размера"""
    for path in ("C:/Windows/Fonts/arialbd.ttf",
                 "C:/Windows/Fonts/seguisb.ttf",
                 "C:/Windows/Fonts/verdanab.ttf"):
        if not os.path.exists(path):
            continue
        lo, hi = 8, 400
        while lo < hi:
            mid = (lo + hi) // 2
            b = ImageFont.truetype(path, mid).getbbox(txt)
            if b[3] - b[1] < target:
                lo = mid + 1
            else:
                hi = mid
        return ImageFont.truetype(path, lo)
    return ImageFont.load_default()


def put_digit(tile, n):
    """цифра по центру клетки, ровно по своим габаритам, без теней"""
    d = ImageDraw.Draw(tile)
    txt = str(n)
    f = font_for_height(txt, GLYPH_H)
    b = f.getbbox(txt)  # рисуем по истинной высоте знака, а не по строке шрифта
    x = SIZE // 2 - (b[0] + b[2]) // 2
    y = SIZE // 2 - (b[1] + b[3]) // 2
    d.text((x, y), txt, font=f, fill=DIGIT_COLORS[n])


def mine_sprite():
    """мина: чёрный шар, восемь шипов, блик"""
    def draw(d, s):
        c = SIZE * s // 2
        w = 3 * s
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            d.line([(c + dx * 12 * s, c + dy * 12 * s),
                    (c + dx * 21 * s, c + dy * 21 * s)], fill=BLACK, width=w)
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            d.line([(c + dx * 10 * s, c + dy * 10 * s),
                    (c + dx * 16 * s, c + dy * 16 * s)], fill=BLACK, width=w)
        r = 13 * s
        d.ellipse([c - r, c - r, c + r, c + r], fill=BLACK)
        d.ellipse([c - 7 * s, c - 7 * s, c - 2 * s, c - 2 * s], fill=HILITE)
    return smooth(draw)


def flag_sprite():
    """флаг: полотнище, флагшток, основание в две ступеньки"""
    def draw(d, s):
        d.polygon([(25 * s, 9 * s), (25 * s, 22 * s), (8 * s, 15 * s)], fill=RED)
        d.rectangle([24 * s, 8 * s, 27 * s, 40 * s], fill=BLACK)
        d.rectangle([18 * s, 36 * s, 33 * s, 40 * s], fill=BLACK)
        d.rectangle([15 * s, 40 * s, 36 * s, 45 * s], fill=BLACK)
    return smooth(draw)


def cross_sprite():
    """красный крест поверх мины - так отмечают неверный флаг"""
    def draw(d, s):
        d.line([(8 * s, 8 * s), (40 * s, 40 * s)], fill=RED, width=4 * s)
        d.line([(40 * s, 8 * s), (8 * s, 40 * s)], fill=RED, width=4 * s)
    return smooth(draw)


def save(img, name):
    img.save(os.path.join(OUT, name + ".png"))


def build():
    # старые тайлы убираем целиком: если оставить лишние closed*,
    # игра подберёт их случайно и поле будет пестрым
    os.makedirs(OUT, exist_ok=True)
    for fn in os.listdir(OUT):
        if fn.endswith(".png"):
            os.remove(os.path.join(OUT, fn))

    made = []

    # раскрытые: пустая клетка и с цифрами
    for n in range(0, 9):
        tile = opened()
        if n:
            put_digit(tile, n)
        save(tile, "n%d" % n)
        made.append("n%d" % n)

    flat = closed()
    save(flat, "closed0")
    made.append("closed0")

    save(over(opened(), mine_sprite()), "mine")
    made.append("mine")

    save(over(flat, flag_sprite()), "flag")
    made.append("flag")

    save(over(over(opened(), mine_sprite()), cross_sprite()), "wrongflag")
    made.append("wrongflag")

    print("tiles built: %d - %s" % (len(made), ", ".join(made)))
    return made


if __name__ == "__main__":
    build()
