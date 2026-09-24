# -*- coding: utf-8 -*-
# сапер в классическом виде: серые плитки с фаской, как в виндовс-сапере
# тайлы рисует build_tiles.py сам, лежат в assets/tiles
#
# запуск: python minesweeper.py
#
# меню (до игры):
#   1-5, стрелки влево/вправо - выбрать размер поля
#   стрелки вверх/вниз        - сколько мин
#   Enter                     - играть
#   Esc                       - выход
#
# игра:
#   ЛКМ - открыть клетку
#   ПКМ - поставить флаг
#   R   - новая игра (работает и в русской раскладке: к)
#   Esc - назад в меню

import os
import random

import turtle
from tkinter import PhotoImage, TclError

HERE = os.path.dirname(os.path.abspath(__file__))
TILE_DIR = os.path.join(HERE, "assets", "tiles")

TILE = 48                 # тайлы собраны под клетку 48 px
SIZES = (8, 16, 32, 64, 128)
# размеры клеток - только делители 48, чтобы Tk уменьшал картинку через subsample
CELL_SIZES = (48, 24, 16, 12, 8, 6, 4, 3, 2)
MENU_W, MENU_H = 640, 470

# цвета как в виндовс-сапере: серое окно, шапка чёрным по серому
BG = "#c0c0c0"
TEXT = "#000000"
HINT = "#404040"
WIN_C = "#006400"
LOSE_C = "#cc0000"
SELECT_C = "#000080"      # выбранная кнопка в меню

FONT = ("Segoe UI", 16, "bold")

_tiles = {}   # картинки клеток по размеру, чтобы файлы не читать заново


def default_mines(size):
    """мин по умолчанию: те же ~15%, что у виндовса"""
    return max(1, round(size * size * 0.15))


def choose_cell(screen, size):
    """подбираем клетку, чтобы поле влезло в экран вместе с шапкой и подсказкой"""
    room_w = screen.cv.winfo_screenwidth() - 80
    room_h = screen.cv.winfo_screenheight() - 190   # шапка, подсказка, панель задач
    for cell in CELL_SIZES:
        if cell * size <= room_w and cell * size <= room_h:
            return cell
    return CELL_SIZES[-1]


def make_screen():
    """окно и холст - всё, что нам от turtle нужно"""
    s = turtle.Screen()
    s.title("Сапер")
    s.bgcolor(BG)
    s.setup(MENU_W, MENU_H)
    return s


def load_tiles(cell):
    """картинки клеток нужного размера.

    исходные тайлы 48 px, меньше берём через subsample - Tk уменьшает сам,
    поэтому Pillow для самой игры не нужна. ссылки держим в словаре: gc,
    убравший PhotoImage, валит tk"""
    if cell in _tiles:
        return _tiles[cell]

    if not os.path.isdir(TILE_DIR) or not os.listdir(TILE_DIR):
        import build_tiles  # тайлов нет - рисуем сами
        build_tiles.build()

    tiles = {}
    for fn in sorted(os.listdir(TILE_DIR)):
        if not fn.endswith(".png"):
            continue
        img = PhotoImage(file=os.path.join(TILE_DIR, fn))
        if cell != TILE:
            img = img.subsample(TILE // cell, TILE // cell)
        tiles[fn[:-4]] = img

    _tiles[cell] = tiles
    return tiles


class Game:
    """вся логика здесь, чтобы не плодить глобальные переменные"""

    def __init__(self, screen, size, mines):
        self.screen = screen
        self.cv = screen.getcanvas()
        self.w = self.h = size
        self.mine_count = mines
        self.cell = choose_cell(screen, size)
        self.tiles = load_tiles(self.cell)

        # окно под поле: запас сверху под шапку, снизу под подсказку.
        # по ширине не уже 480 - подсказка 416 px, на поле 8x8 (424 px)
        # она упиралась в края
        win_w = max(size * self.cell + 40, 480)
        self.screen.setup(win_w, size * self.cell + 140)

        # mines - где бомбы, opened - что открыли, flags - что помечено
        self.mines = set()
        self.opened = set()
        self.flags = set()
        self.dead = False
        self.won = False
        self.placed = False  # мины ставим после первого клика, иначе можно проиграть сразу

        self.cells = {}   # клетка -> картинка на холсте
        self.draw()

        self.restart()

    def draw(self):
        """кладём поле на холст картинками.

        клетки-черепашки здесь не годятся: 16384 черепахи дают секунду на
        каждый перерисовку (см. bench.py против bench_canvas.py), а одна
        картинка на клетку обновляется за сотые доли - поле 128x128 играбельно"""
        self.cv.update_idletasks()  # холст должен подрасти под новое окно

        # поле рисуем по центру окна: холст у turtle центрируется на 0,0
        center_x = self.cv.canvasx(self.cv.winfo_width() / 2)
        center_y = self.cv.canvasy(self.cv.winfo_height() / 2)
        self.ox = center_x - self.w * self.cell // 2   # левый край поля
        self.oy = center_y - self.h * self.cell // 2   # верхний край поля

        closed = self.tiles["closed0"]
        for y in range(self.h):
            for x in range(self.w):
                cx = self.ox + x * self.cell + self.cell // 2
                cy = self.oy + y * self.cell + self.cell // 2
                item = self.cv.create_image(cx, cy, image=closed, tags="board")
                self.cells[(x, y)] = item

        self.hud = self.cv.create_text(center_x, self.oy - 45, text="",
                                       fill=TEXT, font=FONT, tags="hud")
        self.hint = self.cv.create_text(
            center_x, self.oy + self.h * self.cell + 55,
            text="ЛКМ - открыть, ПКМ - флаг, R - заново, Esc - в меню",
            fill=HINT, font=("Segoe UI", 13), tags="hud")

    def destroy(self):
        """снимаем игру с холста, освобождая место под меню"""
        self.cv.delete("board")
        self.cv.delete("hud")
        self.cells.clear()

    def cell_at(self, event):
        """какая клетка под курсором, или None если мимо поля"""
        x = int((self.cv.canvasx(event.x) - self.ox) // self.cell)
        y = int((self.cv.canvasy(event.y) - self.oy) // self.cell)
        if 0 <= x < self.w and 0 <= y < self.h:
            return x, y
        return None

    def neighbors(self, x, y):
        """все соседи клетки, но только внутри поля"""
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.w and 0 <= ny < self.h:
                    yield nx, ny

    def place_mines(self, safe):
        """ставим мины, safe - клетка первого клика и её соседи, туда не ставим"""
        banned = {safe} | set(self.neighbors(*safe))
        free = [(x, y) for x in range(self.w)
                for y in range(self.h) if (x, y) not in banned]
        self.mines = set(random.sample(free, min(self.mine_count, len(free))))
        self.placed = True

    def count(self, x, y):
        """сколько мин вокруг клетки"""
        return sum(1 for n in self.neighbors(x, y) if n in self.mines)

    def restart(self):
        """новая игра, все сбрасываем"""
        self.mines.clear()
        self.opened.clear()
        self.flags.clear()
        self.dead = False
        self.won = False
        self.placed = False

        closed = self.tiles["closed0"]
        for item in self.cells.values():
            self.cv.itemconfig(item, image=closed)  # возвращаем закрытую плитку

        self.update_hud()

    def update_hud(self):
        left = self.mine_count - len(self.flags)
        if self.dead:
            text, color = "БАБАХ! жми R чтобы заново, Esc - меню", LOSE_C
        elif self.won:
            text, color = "ПОБЕДА! жми R чтобы еще, Esc - меню", WIN_C
        else:
            text, color = "%d×%d  мин осталось: %d" % (self.w, self.h, left), TEXT
        self.cv.itemconfig(self.hud, text=text, fill=color)

    def set_tile(self, key, name):
        """кладём другой тайл на клетку"""
        self.cv.itemconfig(self.cells[key], image=self.tiles[name])

    def flag(self, key):
        if key in self.flags:
            self.flags.discard(key)
            self.set_tile(key, "closed0")  # сняли - снова закрытая плитка
        else:
            self.flags.add(key)
            self.set_tile(key, "flag")

    def click(self, x, y, btn):
        if self.dead or self.won:
            return

        key = (x, y)

        if btn == 3:  # правая кнопка - флаг
            if key not in self.opened:
                self.flag(key)
                self.update_hud()
            return

        if key in self.flags or key in self.opened:
            return  # флагнутую или открытую просто так не открываем

        if not self.placed:
            self.place_mines(key)

        if key in self.mines:
            self.lose(key)
        else:
            self.flood(key)
            self.check_win()

    def flood(self, key):
        """открываем пустую область вокруг клетки. дальше заливка идёт только
        из нулей: цифра - это край области, через неё не лезем, иначе
        за один клик откроется вся половина поля"""
        stack = [key]
        while stack:
            k = stack.pop()
            if k in self.opened or k in self.flags or k in self.mines:
                continue
            self.opened.add(k)

            x, y = k
            n = self.count(x, y)
            # цифра уже нарисована на тайле, цветом её красить не надо
            self.set_tile(k, "n%d" % n)
            if n == 0:  # пустая клетка - разливаемся дальше
                stack.extend(self.neighbors(x, y))

    def check_win(self):
        # открыли всё что не мина
        if len(self.opened) == self.w * self.h - len(self.mines):
            self.won = True
            # оставшиеся мины помечаем флагами
            for m in self.mines - self.flags:
                self.flags.add(m)
                self.set_tile(m, "flag")
            self.update_hud()

    def lose(self, key):
        self.dead = True
        # показываем мины (кроме правильно помеченных - там флаг остается)
        for m in self.mines - self.flags:
            self.set_tile(m, "mine")
        # неправильные флаги помечаем крестом
        for f in self.flags - self.mines:
            self.set_tile(f, "wrongflag")
        self.update_hud()


class Menu:
    """выбор поля: размер и сколько мин"""

    def __init__(self, screen, on_start):
        self.screen = screen
        self.cv = screen.getcanvas()
        self.on_start = on_start
        self.size = SIZES[0]
        self.mines = default_mines(self.size)
        self.draw()

    def hide(self):
        self.cv.delete("menu")

    def max_mines(self):
        """мин должно хватить на поле: у первого клика 9 безопасных клеток"""
        return self.size * self.size - 9

    def step(self):
        """на сколько прыгает число мин по кнопке или стрелке"""
        return max(1, self.size * self.size // 100)

    def set_size(self, size):
        self.size = size
        self.mines = default_mines(size)  # под новым размером мин считаем заново
        self.draw()

    def set_mines(self, value):
        self.mines = max(1, min(self.max_mines(), value))
        self.draw()

    def press(self, tag):
        """клик по кнопке меню"""
        if tag.startswith("size"):
            self.set_size(int(tag[4:]))
        elif tag == "minus":
            self.set_mines(self.mines - self.step())
        elif tag == "plus":
            self.set_mines(self.mines + self.step())
        elif tag == "play":
            self.on_start(self.size, self.mines)

    def key(self, event):
        """клавиши меню: цифры и стрелки выбирают, Enter играет"""
        ch = (event.char or "").lower()
        key = event.keysym
        if ch and ch in "12345" and int(ch) <= len(SIZES):
            self.set_size(SIZES[int(ch) - 1])
        elif key in ("Left", "Right"):
            i = SIZES.index(self.size) + (1 if key == "Right" else -1)
            self.set_size(SIZES[i % len(SIZES)])
        elif key == "Up":
            self.set_mines(self.mines + self.step())
        elif key == "Down":
            self.set_mines(self.mines - self.step())
        elif key in ("Return", "space"):
            self.on_start(self.size, self.mines)

    def draw(self):
        cv = self.cv
        cv.delete("menu")
        cx = cv.canvasx(cv.winfo_width() / 2)   # центр окна в координатах холста
        cy = cv.canvasy(cv.winfo_height() / 2)

        cv.create_text(cx, cy - 190, text="Сапер", fill=TEXT,
                       font=("Segoe UI", 30, "bold"), tags="menu")
        cv.create_text(cx, cy - 135, text="Размер поля", fill=TEXT,
                       font=FONT, tags="menu")

        # пять кнопок в ряд: по 112 px с зазором 6, ряд по центру окна
        for i, size in enumerate(SIZES):
            selected = size == self.size
            self.button(cx - 236 + i * 118, cy - 85, 112, 44,
                        "%d×%d" % (size, size), "size%d" % size,
                        fill=SELECT_C if selected else BG,
                        color="#ffffff" if selected else TEXT)

        cells = self.size * self.size
        cv.create_text(cx, cy - 25, text="Мин", fill=TEXT, font=FONT, tags="menu")
        self.button(cx - 150, cy + 30, 44, 44, "-", "minus")
        cv.create_text(cx, cy + 30,
                       text="%d (%d%%)" % (self.mines, self.mines * 100 // cells),
                       fill=TEXT, font=("Segoe UI", 22, "bold"), tags="menu")
        self.button(cx + 150, cy + 30, 44, 44, "+", "plus")

        self.button(cx, cy + 125, 240, 56, "Играть", "play",
                    font=("Segoe UI", 20, "bold"))
        cv.create_text(cx, cy + 190,
                       text="цифры и стрелки выбирают, Enter - играть, Esc - выход",
                       fill=HINT, font=("Segoe UI", 13), tags="menu")

    def button(self, x, y, w, h, text, tag, fill=BG, color=TEXT, font=FONT):
        """кнопка с фаской, как в виндовс-диалоге.

        все куски кнопки (прямоугольник, фаска, надпись) получают её тег:
        иначе надпись сверху перехватит клик и прямоугольник не сработает"""
        cv = self.cv
        x1, y1 = x - w // 2, y - h // 2
        x2, y2 = x + w // 2, y + h // 2
        cv.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#000000",
                            tags=(tag, "menu"))
        cv.create_line(x1 + 2, y1 + 2, x2 - 2, y1 + 2, fill="#ffffff",
                       tags=(tag, "menu"))
        cv.create_line(x1 + 2, y1 + 2, x1 + 2, y2 - 2, fill="#ffffff",
                       tags=(tag, "menu"))
        cv.create_line(x1 + 2, y2 - 2, x2 - 2, y2 - 2, fill="#808080",
                       tags=(tag, "menu"))
        cv.create_line(x2 - 2, y1 + 2, x2 - 2, y2 - 2, fill="#808080",
                       tags=(tag, "menu"))
        cv.create_text(x, y, text=text, fill=color, font=font, tags=(tag, "menu"))
        cv.tag_bind(tag, "<Button-1>", lambda event, t=tag: self.press(t))


class App:
    """окно целиком: держит меню и текущую игру, между ними переключаемся по Esc"""

    def __init__(self, screen):
        self.screen = screen
        self.cv = screen.getcanvas()
        self.game = None
        self.menu = None

        # клики и клавиши ловим один раз на холсте (фокус на нём после listen)
        self.cv.bind("<Button-1>", lambda e: self.on_click(e, 1))
        self.cv.bind("<Button-3>", lambda e: self.on_click(e, 3))
        self.cv.bind("<KeyPress>", self.on_key)

        self.show_menu()

    def on_click(self, event, btn):
        if self.game:
            key = self.game.cell_at(event)
            if key:
                self.game.click(*key, btn)

    def on_key(self, event):
        """русскую раскладку через onkeypress не забиндить (tk ругается на
        keysym), поэтому читаем символ общим обработчиком как в змейке"""
        ch = (event.char or "").lower()
        if self.game:
            if ch in ("r", "к"):
                self.game.restart()
            elif event.keysym == "Escape":
                self.show_menu()
        elif self.menu:
            if event.keysym == "Escape":
                self.quit()
            else:
                self.menu.key(event)

    def show_menu(self):
        if self.game:
            self.game.destroy()
            self.game = None
        # сначала убираем старую игру, потом ресайз - внутри setup прогоняет
        # события, и обработчик не должен наткнуться на полумёртвую игру
        self.menu = None
        self.screen.setup(MENU_W, MENU_H)
        self.menu = Menu(self.screen, self.start)

    def start(self, size, mines):
        self.menu.hide()
        self.menu = None
        self.game = Game(self.screen, size, mines)

    def quit(self):
        self.screen.bye()  # тут цикла нет, только mainloop, поэтому можно сразу


def main():
    screen = make_screen()
    app = App(screen)
    screen.listen()  # фокус на холсте, без него клавиши не приходят
    screen.cv.master.protocol("WM_DELETE_WINDOW", app.quit)
    screen.mainloop()


if __name__ == "__main__":
    try:
        main()
    except TclError:
        pass  # окно закрыли пока рисовали, не страшно
