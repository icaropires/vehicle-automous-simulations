import tkinter

# px
WINDOW_H = 900
WINDOW_W = 900
DISTANCE_BORDERS = 200
RADIUS_ACTIVATOR = 10


def add_activators(canvas):
    return [
        canvas.create_oval(
            DISTANCE_BORDERS-RADIUS_ACTIVATOR,
            DISTANCE_BORDERS-RADIUS_ACTIVATOR,
            DISTANCE_BORDERS+RADIUS_ACTIVATOR,
            DISTANCE_BORDERS+RADIUS_ACTIVATOR,
            fill="blue"
        ),
        canvas.create_oval(
            WINDOW_W-DISTANCE_BORDERS-RADIUS_ACTIVATOR,
            DISTANCE_BORDERS-RADIUS_ACTIVATOR,
            WINDOW_W-DISTANCE_BORDERS+RADIUS_ACTIVATOR,
            DISTANCE_BORDERS+RADIUS_ACTIVATOR,
            fill="blue"
        ),
        canvas.create_oval(
            WINDOW_W-DISTANCE_BORDERS-RADIUS_ACTIVATOR,
            WINDOW_H-DISTANCE_BORDERS-RADIUS_ACTIVATOR,
            WINDOW_W-DISTANCE_BORDERS+RADIUS_ACTIVATOR,
            WINDOW_H-DISTANCE_BORDERS+RADIUS_ACTIVATOR,
            fill="blue"
        ),
        canvas.create_oval(
            DISTANCE_BORDERS-RADIUS_ACTIVATOR,
            WINDOW_H-DISTANCE_BORDERS-RADIUS_ACTIVATOR,
            DISTANCE_BORDERS+RADIUS_ACTIVATOR,
            WINDOW_H-DISTANCE_BORDERS+RADIUS_ACTIVATOR,
            fill="blue"
        ),
    ]


window = tkinter.Tk()

window.title('GUI')

canvas = tkinter.Canvas(window, bg="white", height=WINDOW_H, width=WINDOW_W)
activators = add_activators(canvas)

canvas.pack()
window.mainloop()
