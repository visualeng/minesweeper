# -*- coding: utf-8 -*-
# замер: сколько стоит нарисовать N клеток обычным canvas (без turtle)
# и как быстро меняется картинка у одной клетки.
#
# запуск: python bench_canvas.py <N> <сторона>
import os
import sys
import time

from tkinter import Tk, PhotoImage, Canvas

N = int(sys.argv[1])
side = int(sys.argv[2])

root = Tk()
root.geometry("600x600")
cv = Canvas(root, bg="#c0c0c0")
cv.pack(fill="both", expand=True)
root.update()

t0 = time.time()
imgs = []
for fn in sorted(os.listdir("assets/tiles")):
    if fn.endswith(".png"):
        imgs.append(PhotoImage(file=os.path.join("assets/tiles", fn)))
t1 = time.time()

cell = max(4, min(48, 560 // side))
items = []
for i in range(N):
    x, y = i % side, i // side
    items.append(cv.create_image(40 + x * cell, 40 + y * cell, image=imgs[0]))
t2 = time.time()

cv.update()
t3 = time.time()

cv.itemconfig(items[N // 2], image=imgs[1])
cv.update()
t4 = time.time()

cv.itemconfig(items[N // 2 + 1], image=imgs[2])
cv.update()
t5 = time.time()

print("canvas N=%d side=%d cell=%d | load %.2fs create %.2fs first_upd %.2fs "
      "change %.2fs change2 %.2fs"
      % (N, side, cell, t1 - t0, t2 - t1, t3 - t2, t4 - t3, t5 - t4))
