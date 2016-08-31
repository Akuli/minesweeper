import collections
import functools
import random
import tkinter as tk
from tkinter import messagebox
import webbrowser


# Core
# ~~~~

class Square:

    def __init__(self, opened=False, mine=False, flagged=False):
        self.opened = opened
        self.mine = mine
        self.flagged = flagged

    def __repr__(self):
        return ('<%s opened=%r mine=%r flagged=%r>'
                % (type(self).__name__, self.opened,
                   self.mine, self.flagged))


class Game:
    """One game that ends in a win or a gameover."""

    def __init__(self, width=9, height=9, mines=10):
        self.width = width
        self.height = height
        self.mines = mines
        all_coords = [(x, y) for x in range(width) for y in range(height)]
        mine_coords = random.sample(all_coords, mines)
        self._squares = {coords: Square() for coords in all_coords}
        for coords in mine_coords:
            self[coords].mine = True

    def __getitem__(self, coords):
        return self._squares[coords]

    def toggle_flag(self, coords):
        if not self[coords].opened:
            self[coords].flagged = not self[coords].flagged

    def open(self, coords):
        if not self[coords].flagged:
            self[coords].opened = True
        if self.number_of_mines_around(coords) == 0:
            self.auto_open(coords)

    def auto_open(self, coords):
        for coords in self.coords_around(coords):
            if not self[coords].opened:
                self.open(coords)

    def coords_around(self, coords):
        centerx, centery = coords
        for xdiff in (-1, 0, 1):
            for ydiff in (-1, 0, 1):
                if xdiff == ydiff == 0:
                    # Center.
                    continue
                x = centerx + xdiff
                y = centery + ydiff
                if x in range(self.width) and y in range(self.height):
                    # The place is on the board, not beyond an edge.
                    yield x, y

    def mines_around(self, coords):
        for minecoords in self.coords_around(coords):
            if self[minecoords].mine:
                yield minecoords

    def number_of_mines_around(self, coords):
        result = 0
        for coords_around in self.mines_around(coords):
            result += 1
        return result

    def all_coords(self):
        return self._squares.keys()

    def explosion_coords(self):
        for coords in self.all_coords():
            if self[coords].mine and self[coords].opened:
                return coords
        return None

    def exploded(self):
        return self.explosion_coords() is not None

    def win(self):
        for coords in self.all_coords():
            if not (self[coords].mine or self[coords].opened):
                return False
        return not self.exploded()

    def over(self):
        return self.exploded() or self.win()


# Tkinter GUI
# ~~~~~~~~~~~

class PlayingArea(tk.Canvas):
    SCALE = 20

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind('<ButtonRelease-1>', self._leftclick)
        self.bind('<ButtonRelease-3>', self._rightclick)
        self.new_game()

    def new_game(self):
        self.game = Game(width=30, height=24, mines=99)
        self['width'] = self.SCALE * self.game.width
        self['height'] = self.SCALE * self.game.height
        self.update()

    def update(self):
        self.delete('all')
        for coords in self.game.all_coords():
            self._draw_square(coords, self.game[coords])
        if self.game.win():
            messagebox.showinfo("Minesweeper", "You won.")
        elif self.game.exploded():
            messagebox.showinfo("Minesweeper", "You lost!")
        else:
            # No new game.
            return
        self.new_game()

    def _draw_square(self, coords, square):
        x, y = coords
        left = x * self.SCALE
        right = x * self.SCALE + self.SCALE
        top = y * self.SCALE
        bottom = y * self.SCALE + self.SCALE
        centerx = (left + right) // 2
        centery = (top + bottom) // 2

        background = '#cccccc'
        text = ''
        if square.opened and square.mine:
            background = 'red'
            text = '*'
        elif square.opened:
            text = str(self.game.number_of_mines_around(coords))

        self.create_rectangle(left, top, right, bottom, fill=background)
        self.create_text(centerx, centery, text=text, fill='black')

        if square.flagged:
            # x=0%      x=50%
            #  |          |
            #  |
            #  0%        ooo        -- y=0%
            #  |      oooooo
            #  |   ooooooooo
            #  |oooooooooooo        -- y=25%
            #  |   ooooooooo
            #  |      oooooo
            # 50%        ooo        -- y=50%
            #  |         ooo
            #  |         ooo
            #  |         ooo
            #  |         ooo
            # 100%       ooo        -- y=100%
            #  |
            #  o---------50%-------100%--
            self.create_polygon(
                centerx, centery,
                centerx, top,
                left, (centery + top) // 2,
                fill='red',
            )
            self.create_line(
                centerx, top,
                centerx, bottom,
                fill='black',
                width=self.SCALE // 10,
            )

    def __click_handler(func):
        # TODO: check if the coords exist
        @functools.wraps(func)
        def inner(self, event):
            if self.game.over():
                return
            x = event.x // self.SCALE
            y = event.y // self.SCALE

            result = None
            if x in range(self.game.width) and y in range(self.game.height):
                # The user isn't clicking on the edge of the playing
                # area.
                coords = x, y
                result = func(self, coords)
                self.update()
            return result
        return inner

    @__click_handler
    def _leftclick(self, coords):
        self.game.open(coords)

    @__click_handler
    def _rightclick(self, coords):
        self.game.toggle_flag(coords)


def wikihow_howto():
    webbrowser.open('http://www.wikihow.com/Play-Minesweeper')


def about():
    messagebox.showinfo("About this game",
                        "This game was written by Akuli.")


def main():
    root = tk.Tk()

    playingarea = PlayingArea(root, bg='white')
    playingarea.pack(fill='both', expand=True)

    menubar = tk.Menu(root)
    root['menu'] = menubar

    menu = tk.Menu(menubar, tearoff=False)
    menu.add_command(label="New game", command=playingarea.new_game)
    menu.add_command(label="Quit", command=root.destroy)
    menubar.add_cascade(label="Game", menu=menu)

    menu = tk.Menu(menubar, tearoff=False)
    menu.add_command(label='"How to play minesweeper" in wikiHow',
                     command=wikihow_howto)
    menu.add_command(label="About", command=about)
    menubar.add_cascade(label="Help", menu=menu)

    root.title("Minesweeper")
    root.resizable(width=False, height=False)
    root.mainloop()


if __name__ == '__main__':
    main()
