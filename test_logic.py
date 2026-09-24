# -*- coding: utf-8 -*-
# быстрая проверка логики сапера, без мыши и без глаз
import random
import minesweeper as m

random.seed(42)
screen = m.make_screen()
g = m.Game(screen)

# --- 1. первый клик не должен быть миной, мины ставятся после клика ---
assert not g.placed
g.click(4, 4, 1)
assert g.placed, "мины должны были установиться после первого клика"
assert (4, 4) not in g.mines, "первый клик не должен быть в мину"
assert len(g.mines) == m.MINES, f"должно быть {m.MINES} мин, got {len(g.mines)}"
# и соседи первого клика тоже должны быть чистыми
assert not (set(g.neighbors(4, 4)) & g.mines), "соседи первого клика должны быть чистыми"
print("1. первый клик безопасен, мины установлены:", len(g.mines))

# --- 2. флуд-филл: пустая клетка открывает область ---
opened_after_first = len(g.opened)
assert opened_after_first >= 1
print("2. флуд открыл клеток:", opened_after_first)

# --- 3. флаг ---
g2 = m.Game(screen)
g2.place_mines((0, 0))  # без клика, чтобы знать мины
mine = next(iter(g2.mines))
g2.flag(mine)
assert mine in g2.flags
g2.flag(mine)  # второй клик снимает
assert mine not in g2.flags, "флаг должен сниматься"
print("3. флаг ставится и снимается")

# --- 4. поражение: клик по мине ---
g3 = m.Game(screen)
g3.place_mines((8, 8))
boom = next(iter(g3.mines))
g3.click(*boom, 1)
assert g3.dead, "должен наступить проигрыш"
print("4. клик по мине -> проигрыш, мин показано:", len(g3.mines - g3.flags))

# --- 5. победа: открыть все не-мины ---
g4 = m.Game(screen)
g4.place_mines((0, 0))
for x in range(m.W):
    for y in range(m.H):
        if (x, y) not in g4.mines and (x, y) not in g4.opened:
            g4.click(x, y, 1)
assert g4.won, "должна быть победа"
assert g4.flags >= g4.mines, "все мины должны быть помечены при победе"
print("5. победа достигнута, флагов:", len(g4.flags))

# --- 6. рестарт чистит состояние ---
g4.restart()
assert not g4.mines and not g4.opened and not g4.flags
assert not g4.dead and not g4.won and not g4.placed
print("6. рестарт все чистит")

# --- 7. клик по уже открытой/флагнутой не меняет состояние ---
g5 = m.Game(screen)
g5.place_mines((4, 4))
g5.flood((0, 0))
n = len(g5.opened)
if g5.opened:
    k = next(iter(g5.opened))
    g5.click(*k, 1)
    assert len(g5.opened) == n, "повторный клик по открытой не должен ничего менять"
print("7. повторные клики игнорируются")

screen.bye()
print("\nВСЕ ТЕСТЫ ПРОШЛИ")
