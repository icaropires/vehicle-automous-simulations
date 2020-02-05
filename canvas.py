import tkinter


class GUI:
    window_h = 900
    window_w = 900

    activator_borders_distance = 200
    activator_color = "blue"
    activator_radius = 10

    transponder_radius = 20
    transponder_color = "red"

    def __init__(self):
        self.window = tkinter.Tk()

        self.window.title("GUI")

        self.canvas = tkinter.Canvas(
            self.window, height=self.window_h, width=self.window_w, bg="white"
        )

        self.activators = self.add_activators()
        self.transponder = self.add_transponder()

        self.canvas.pack()

    def run(self):
        self.canvas.after(300, self._handle_update)
        self.window.mainloop()

    def _move_transponder(self):
        r = self.transponder_radius
        x, y, *_ = self.canvas.coords(self.transponder)

        x += 1
        y = (x / 20) ** 2

        coords = (x, y, x + 2 * r, y + 2 * r)
        self.canvas.coords(self.transponder, coords)

    def _handle_update(self):
        self._move_transponder()
        self.canvas.after(10, self._handle_update)

    def add_transponder(self):
        r = self.transponder_radius

        return self.canvas.create_oval(
            0, 0, 2 * r, 2 * r, fill=self.transponder_color
        )

    def add_activators(self):
        d = self.activator_borders_distance
        r = self.activator_radius
        ww = self.window_w
        wh = self.window_h
        fill = self.activator_color

        # Like rectangle corners
        coords = (
            (d - r, d - r, d + r, d + r),
            (ww - d - r, d - r, ww - d + r, d + r),
            (ww - d - r, wh - d - r, ww - d + r, wh - d + r),
            (d - r, wh - d - r, d + r, wh - d + r),
        )

        return [self.canvas.create_oval(c, fill=fill) for c in coords]


gui = GUI()
gui.run()
