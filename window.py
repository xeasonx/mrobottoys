import tkinter
from tkinter import *
from tkinter import ttk


class MainWindow:
    def __init__(self):
        self.window = Tk()
        self.window.option_add("*tearOff", FALSE)
        self.window.geometry("800x600")
        self.window.minsize(width=800, height=600)
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.grid(column=0, row=0, sticky=(N, W, E, S))
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.columnconfigure(2, weight=1)
        self.main_frame.columnconfigure(3, weight=1)
        self.main_frame.rowconfigure(0, weight=3)
        self.main_frame.rowconfigure(1, weight=3)
        self.main_frame.rowconfigure(2, weight=1)
        self.main_frame["padding"] = 5

    def _setup_menu(self):
        menubar = Menu(self.main_frame)
        self.window["menu"] = menubar
        menu_help = Menu(menubar)
        menu_file = Menu(menubar)
        menubar.add_cascade(menu=menu_file, label="File")
        menubar.add_cascade(menu=menu_help, label="Help")
        menu_help.add_command(label="About")

    def _setup_canvas(self):
        canvas_pane = ttk.Panedwindow(self.main_frame, orient=VERTICAL)
        canvas_pane.grid(column=0, row=0, columnspan=3, rowspan=3, sticky=(N, W, E, S), padx=5, pady=5)
        canvas_pane.columnconfigure(0, weight=1)
        canvas_pane.rowconfigure(0, weight=1)
        canvas_pane_frame = ttk.LabelFrame(canvas_pane, text="Plot")
        canvas_pane_frame.grid(column=0, row=0, sticky=(N, W, E, S))
        canvas_pane_frame.columnconfigure(0, weight=1)
        canvas_pane_frame.rowconfigure(0, weight=1)
        canvas_pane.add(canvas_pane_frame)
        canvas = Canvas(canvas_pane_frame, width=500, height=400)
        canvas.grid(column=0, row=0, sticky=(N, W, E, S))
        canvas.create_line(10, 5, 200, 50)

    def _setup_options(self):
        options_pane = ttk.Panedwindow(self.main_frame, orient=VERTICAL)
        options_pane.grid(column=3, row=0, rowspan=3, sticky=(N, W, E, S), padx=5, pady=5)
        options_pane.columnconfigure(0, weight=1)
        options_pane.rowconfigure(0, weight=1)
        options_pane_frame = ttk.LabelFrame(options_pane, text="Options")
        options_pane_frame.grid(column=0, row=0, sticky=(N, W, E, S))
        options_pane_frame.columnconfigure(0, weight=1)
        options_pane_frame.rowconfigure(0, weight=1)
        options_pane.add(options_pane_frame)
        v = StringVar()
        ttk.Label(options_pane_frame, text="option").grid(column=0, row=0, sticky=(W, N))
        ttk.Entry(options_pane_frame, textvariable=v).grid(column=1, row=0, sticky=(W, N))

    def _setup_logs(self):
        text_frame = ttk.Frame(self.main_frame)
        text_frame.grid(column=0, row=2, columnspan=4, sticky=(N, W, E, S), padx=5)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        text = Text(text_frame, height=15)
        text.grid(column=0, row=0, sticky=(N, W, E, S))
        text.insert('1.0', 'here is my\ntext to insert')

    def start(self):
        self._setup_menu()
        self._setup_canvas()
        self._setup_options()
        self._setup_logs()
        self.window.mainloop()


if __name__ == '__main__':
    w = MainWindow()
    w.start()
