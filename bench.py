# -*- coding: utf-8 -*-
# замер: сколько стоит создать N черепах-клеток и обновить экран.
# нужен, чтобы решить - тянет ли turtle поле 128x128 (16384 клетки).
#
# запуск: python bench.py <N> <сторона>
import os
import sys
import time

import turtle
from tkinter import PhotoImage

N = int(sys.argv[1])
side = int(sys.argv[2])

s = turtle.Screen()
s.setup(600, 600)
s.tracer(0)
cv = s.getcanvas()

t0 = time.time()
for fn in sorted(os.listdir("assets/tiles")):
    if fn.endswith(".png"):
        img = PhotoImage(file=os.path.join("assets/tiles", fn))
        s.register_shape(fn[:-4], turtle.Shape("image", img))
t1 = time.time()

cell = max(4, min(48, 560 // side))
cells = []
for i in range(N):
    x, y = i % side, i // side
    t = turtle.Turtle()
    t.penup()
    t.shape("closed0")
    t.goto(-280 + cell // 2 + x * cell, 280 - cell // 2 - y * cell)
    t.onclick(lambda *a: None, btn=1)
    t.onclick(lambda *a: None, btn=3)
    cells.append(t)
t2 = time.time()

s.update()
t3 = time.time()

cells[N // 2].shape("n1")
s.update()
t4 = time.time()

s.update()
t5 = time.time()

print("N=%d side=%d cell=%d | register %.2fs create %.2fs first_upd %.2fs "
      "change_upd %.2fs noop_upd %.2fs"
      % (N, side, cell, t1 - t0, t2 - t1, t3 - t2, t4 - t3, t5 - t4))
