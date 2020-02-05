import sys
import csv
import tkinter


class GUI:
    window_h = 900
    window_w = 900

    activator_borders_distance = 200
    activator_color = "blue"
    activator_radius = 10

    transponder_radius = 20
    transponder_color = "red"

    default_filename = "data.csv"

    csv_window_w = 1800
    csv_window_h = 1800
    scale_from_csv = window_h / csv_window_h  # Assuming width = height

    measurements_interval = 200

    def __init__(self):
        self.window = tkinter.Tk()
        self.window.title("GUI")

        self.canvas = tkinter.Canvas(
            self.window, height=self.window_h, width=self.window_w, bg="white"
        )

        self.activators = self.add_activators()
        self.transponder = self.add_transponder()

        self.canvas.pack()

        self.datafile = self.read_datafile()

        self._progress_bar = None

    def run(self):
        self.canvas.after(300, self._handle_update)
        self.window.mainloop()

    def _move_transponder(self):
        r = self.transponder_radius

        try:
            x, y = next(self.datafile)
        except StopIteration:
            x, y = (-self.window_w, -self.window_h)

        coords = (x - r, y - r, x + r, y + r)
        self.canvas.coords(self.transponder, coords)

        print("New coords:", x, y)

    def _handle_update(self):
        self._move_transponder()
        self.canvas.after(self.measurements_interval, self._handle_update)

    def add_transponder(self):
        r = self.transponder_radius
        ww = self.window_w
        wh = self.window_h

        x, y = -ww, -wh

        return self.canvas.create_oval(
            x, y, x + 2 * r, y + 2 * r, fill=self.transponder_color
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

    def read_datafile(self):
        filename = self.default_filename

        if len(sys.argv) > 1:
            filename = sys.argv[1]

        with open(filename, "r") as f:
            rows = csv.DictReader(f)

            content = [
                (int(r["estimated_x"]), int(r["estimated_y"]))
                for r in rows
                if int(r["id_activator"]) == 1
            ]

        # To generator and correct scale
        content = (
            (x * self.scale_from_csv, y * self.scale_from_csv)
            for x, y in content
        )

        return content


gui = GUI()
gui.run()
