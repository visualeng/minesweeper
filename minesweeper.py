# -*- coding: utf-8 -*-
# сапер на python, делал чтобы поиграть и потренироваться
# запуск: python minesweeper.py
#
# управление:
#   ЛКМ - открыть клетку
#   ПКМ - поставить флаг
#   R   - новая игра
#   Esc - выход

import random
import turtle
from tkinter import TclError

# поле 9x9 и 10 мин, как в виндовс сапере
W = 9
H = 9
MINES = 10
CELL = 40  # размер клетки в пикселях

# цвета, взял тему как в змейке
BG = "#1a1a2e"
CLOSED = "#3b4263"
OPENED = "#242b45"
BOMB_BG = "#e94560"
FLAG_BG = "#f0883e"
TEXT = "#e6edf3"
ACCENT = "#00d4aa"

# цифры раскрашиваем как в нормальном сапере
NUM_COLORS = {
    1: "#6cb6ff",
    2: "#7ee787",
    3: "#ff7b72",
    4: "#a5d6ff",
    5: "#ff9bce",
    6: "#76e3ea",
    7: "#d2a8ff",
    8: "#8b949e",
}


def draw_text(pen, text, y, size=18, color=TEXT):
    """пишет надпись по центру экрана (для шапки и подсказок)"""
    pen.clear()
    pen.goto(0, y)
    pen.color(color)
    pen.write(text, align="center", font=("Segoe UI", size, "bold"))


def label(t, text, color):
    """пишет текст в самой клетке. внимание: write() не принимает fill,
    цвет берется от цвета черепахи, поэтому ставим pencolor и сразу возвращаем"""
    old = t.pencolor()
    t.pencolor(color)
    t.write(text, align="center", font=("Segoe UI", 16, "bold"))
    t.pencolor(old)


def make_screen():
    w = W * CELL + 40
    h = H * CELL + 140  # запас сверху под шапку и снизу под подсказку
    s = turtle.Screen()
    s.title("Сапер")
    s.bgcolor(BG)
    s.setup(w, h)
    s.tracer(0)  # без этого тормозит
    return s


class Game:
    """вся логика здесь, чтобы не плодить глобальные переменные"""

    def __init__(self, screen):
        self.screen = screen
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.penup()

        # mines - где бомбы, opened - что открыли, flags - что помечено
        self.mines = set()
        self.opened = set()
        self.flags = set()
        self.dead = False
        self.won = False
        self.placed = False  # мины ставим после первого клика, иначе можно проиграть сразу

        # клетки - это черепашки, словарь по координатам
        self.cells = {}
        top_y = H * CELL // 2 - CELL // 2  # верхний ряд
        for y in range(H):
            for x in range(W):
                t = turtle.Turtle()
                t.speed(0)
                t.penup()
                t.shape("square")
                t.shapesize((CELL - 2) / 20)  # 20 - базовый размер квадрата turtle
                t.color(CLOSED)
                px = -W * CELL // 2 + CELL // 2 + x * CELL
                py = top_y - y * CELL
                t.goto(px, py)
                # лямбда с захватом координат по умолчанию, иначе все клетки
                # будут открывать последнюю (классическая ошибка с замыканием)
                t.onclick(lambda px, py, cx=x, cy=y: self.click(cx, cy, 1), btn=1)
                t.onclick(lambda px, py, cx=x, cy=y: self.click(cx, cy, 3), btn=3)
                self.cells[(x, y)] = t

        self.restart()

    def neighbors(self, x, y):
        """все соседи клетки, но только внутри поля"""
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H:
                    yield nx, ny

    def place_mines(self, safe):
        """ставим мины, safe - клетка первого клика и её соседи, туда не ставим"""
        banned = {safe} | set(self.neighbors(*safe))
        free = [(x, y) for x in range(W) for y in range(H) if (x, y) not in banned]
        self.mines = set(random.sample(free, min(MINES, len(free))))
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

        for t in self.cells.values():
            t.clear()
            t.color(CLOSED)

        self.update_hud()
        self.screen.update()

    def update_hud(self):
        left = MINES - len(self.flags)
        if self.dead:
            draw_text(self.pen, "БАБАХ! жми R чтобы заново",
                      H * CELL // 2 + 45, 16, BOMB_BG)
        elif self.won:
            draw_text(self.pen, "ПОБЕДА! жми R чтобы еще",
                      H * CELL // 2 + 45, 16, ACCENT)
        else:
            draw_text(self.pen, f"Мин осталось: {left}",
                      H * CELL // 2 + 45, 16, TEXT)

    def flag(self, key):
        t = self.cells[key]
        if key in self.flags:
            self.flags.discard(key)
            t.clear()
            t.color(CLOSED)
        else:
            self.flags.add(key)
            t.color(FLAG_BG)
            label(t, "F", "#1a1a2e")

    def click(self, x, y, btn):
        if self.dead or self.won:
            return

        key = (x, y)

        if btn == 3:  # правая кнопка - флаг
            if key not in self.opened:
                self.flag(key)
                self.update_hud()
                self.screen.update()
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

        self.screen.update()

    def flood(self, key):
        """открываем клетку и все пустые вокруг, пока не упрёмся в цифры"""
        stack = [key]
        while stack:
            k = stack.pop()
            if k in self.opened or k in self.flags or k in self.mines:
                continue
            self.opened.add(k)

            x, y = k
            t = self.cells[k]
            t.color(OPENED)
            n = self.count(x, y)
            if n:
                # цвет клетки и цвет текста разные, поэтому сначала fill тут не сработал бы
                label(t, str(n), NUM_COLORS[n])
            else:
                # пустая - расширяемся дальше
                stack.extend(self.neighbors(x, y))

    def check_win(self):
        # открыли всё что не мина
        if len(self.opened) == W * H - len(self.mines):
            self.won = True
            # оставшиеся мины помечаем флагами
            for m in self.mines - self.flags:
                self.flags.add(m)
                t = self.cells[m]
                t.color(FLAG_BG)
                label(t, "F", "#1a1a2e")
            self.update_hud()

    def lose(self, key):
        self.dead = True
        # показываем мины (кроме правильно помеченных - там флаг остается)
        for m in self.mines - self.flags:
            t = self.cells[m]
            t.clear()
            t.color(BOMB_BG)
            label(t, "*", TEXT)
        # мина по которой кликнули - ярче
        if key in self.mines:
            self.cells[key].color("#ff6b6b")
        # неправильные флаги помечаем
        for f in self.flags - self.mines:
            t = self.cells[f]
            t.clear()
            t.color(CLOSED)
            label(t, "?", BOMB_BG)
        self.update_hud()


def main():
    screen = make_screen()

    hint = turtle.Turtle()
    hint.hideturtle()
    hint.penup()
    draw_text(hint, "ЛКМ - открыть, ПКМ - флаг, R - заново",
              -H * CELL // 2 - 55, 13, "#8b949e")

    game = Game(screen)

    def quit_game():
        screen.bye()  # тут цикла нет, только mainloop, поэтому можно сразу

    # русскую раскладку через onkeypress не забиндить (tk ругается на keysym),
    # поэтому ловим символ общим обработчиком как в змейке
    def handle_key(event):
        ch = (event.char or "").lower()
        if ch in ("r", "к"):
            game.restart()

    screen.listen()
    screen.onkeypress(quit_game, "Escape")
    screen.cv.bind("<KeyPress>", handle_key)
    screen.cv.master.protocol("WM_DELETE_WINDOW", quit_game)

    screen.update()
    screen.mainloop()


if __name__ == "__main__":
    try:
        main()
    except TclError:
        pass  # окно закрыли пока рисовали, не страшно
