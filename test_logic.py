# -*- coding: utf-8 -*-
# быстрая проверка логики сапера, без мыши и без глаз
import random
import minesweeper as m

random.seed(42)
screen = m.make_screen()
SIZE = 16          # в тестах поле одинаковое, мин по умолчанию как в игре
g = m.Game(screen, SIZE, m.default_mines(SIZE))

# --- 1. первый клик не должен быть миной, мины ставятся после клика ---
assert not g.placed
g.click(4, 4, 1)
assert g.placed, "мины должны были установиться после первого клика"
assert (4, 4) not in g.mines, "первый клик не должен быть в мину"
assert len(g.mines) == g.mine_count, f"должно быть {g.mine_count} мин, got {len(g.mines)}"
# и соседи первого клика тоже должны быть чистыми
assert not (set(g.neighbors(4, 4)) & g.mines), "соседи первого клика должны быть чистыми"
print("1. первый клик безопасен, мины установлены:", len(g.mines))

# --- 2. флуд-филл: пустая клетка открывает область ---
opened_after_first = len(g.opened)
assert opened_after_first >= 1
print("2. флуд открыл клеток:", opened_after_first)

# --- 3. флаг ---
g2 = m.Game(screen, SIZE, m.default_mines(SIZE))
g2.place_mines((0, 0))  # без клика, чтобы знать мины
mine = next(iter(g2.mines))
g2.flag(mine)
assert mine in g2.flags
g2.flag(mine)  # второй клик снимает
assert mine not in g2.flags, "флаг должен сниматься"
print("3. флаг ставится и снимается")

# --- 4. поражение: клик по мине ---
g3 = m.Game(screen, SIZE, m.default_mines(SIZE))
g3.place_mines((8, 8))
boom = next(iter(g3.mines))
g3.click(*boom, 1)
assert g3.dead, "должен наступить проигрыш"
print("4. клик по мине -> проигрыш, мин показано:", len(g3.mines - g3.flags))

# --- 5. победа: открыть все не-мины ---
g4 = m.Game(screen, SIZE, m.default_mines(SIZE))
g4.place_mines((0, 0))
for x in range(g4.w):
    for y in range(g4.h):
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
g5 = m.Game(screen, SIZE, m.default_mines(SIZE))
g5.place_mines((4, 4))
g5.flood((0, 0))
n = len(g5.opened)
if g5.opened:
    k = next(iter(g5.opened))
    g5.click(*k, 1)
    assert len(g5.opened) == n, "повторный клик по открытой не должен ничего менять"
print("7. повторные клики игнорируются")

# --- 8. флуд-филл останавливается на цифрах, а не пролетает поле ---
# ставим сплошную стену мин по колонке x=3: слева нули, потом цифры, потом опять
# нули. заливка должна открыть нули и прилегающие цифры, но не дойти до правой части
g6 = m.Game(screen, SIZE, m.default_mines(SIZE))
g6.mines = {(3, y) for y in range(g6.h)}
g6.placed = True
g6.flood((0, 0))
assert (2, 0) in g6.opened, "цифра-граница должна открыться"
assert (4, 0) not in g6.opened, "за цифрой заливка идти не должна"
assert len(g6.opened) < g6.w * g6.h - len(g6.mines), "нельзя открыть всё поле одним флудом"
print("8. флуд встал на цифрах, открыто клеток:", len(g6.opened))

# --- 9. первый клик не даёт победу сразу ---
g7 = m.Game(screen, SIZE, m.default_mines(SIZE))
g7.click(7, 7, 1)
assert not g7.won, "победа сразу после первого клика - поле открывалось целиком"
print("9. после первого клика победы нет, открыто:", len(g7.opened),
      "из", g7.w * g7.h - g7.mine_count)

# --- 10. меню: мин не может быть больше, чем клеток, кроме первого клика ---
started = []
screen.setup(m.MENU_W, m.MENU_H)
menu = m.Menu(screen, lambda size, mines: started.append((size, mines)))
menu.set_size(8)
assert menu.mines == m.default_mines(8), "после смены размера мин считаются заново"
menu.set_mines(10 ** 6)          # упирается в потолок
assert menu.mines == menu.max_mines() == 8 * 8 - 9, "потолок - это место под первый клик"
menu.set_mines(0)                # пол
assert menu.mines == 1, "мин не может быть меньше единицы"
menu.set_mines(55)               # и ещё раз вручную, чтобы проверить сам запуск
menu.press("play")
assert started == [(8, 55)], "по кнопке Играть уходит выбранный размер и мин"
menu.hide()
print("10. меню держит число мин в границах поля")

# --- 11. клавиши меню выбирают размер и меняют мин ---
ev = type("Event", (), {})()     # фейковое событие клавиатуры, хватает keysym/char
menu = m.Menu(screen, lambda size, mines: started.append((size, mines)))
ev.keysym, ev.char = "Right", ""
menu.key(ev)
assert menu.size == 16, "стрелка вправо двигает по списку размеров"
ev.keysym, ev.char = "", "4"
menu.key(ev)
assert menu.size == 64, "цифра 4 выбирает поле 64x64"
ev.keysym, ev.char = "Up", ""
menu.key(ev)
assert menu.mines == m.default_mines(64) + 64 * 64 // 100, "стрелка вверх добавляет мин"
ev.keysym, ev.char = "Return", ""
menu.key(ev)
assert started[-1] == (64, menu.mines), "Enter запускает игру с выбранным"
menu.hide()
print("11. клавиши меню работают")

# --- 12. поле и клетка подбираются под экран ---
sw = screen.cv.winfo_screenwidth()
sh = screen.cv.winfo_screenheight()
for size in m.SIZES:
    cell = m.choose_cell(screen, size)
    assert m.TILE % cell == 0, f"клетка {cell} не делит тайл - картинку не уменьшить"
    assert cell * size + 40 <= sw, f"поле {size}x{size} не влезает по ширине"
    assert cell * size + 140 <= sh, f"поле {size}x{size} не влезает по высоте"
print("12. для всех полей клетка подобрана под экран")

screen.bye()
print("\nВСЕ ТЕСТЫ ПРОШЛИ")
