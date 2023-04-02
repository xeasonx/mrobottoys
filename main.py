import os
import tkinter.filedialog

from pathlib import Path
from tkinter import *
from tkinter import ttk
from custom_dialog import remote_dialog, ParamHolder, SSHWrapper, stop_file_thread

home_dir = os.listdir("/home/eason")
param_holder = ParamHolder()
ssh_wrapper = SSHWrapper()


def handle_open_file(x):
    filepath = Path(file_tree.focus())
    if filepath.exists() and filepath.is_file():
        text_widget.delete("1.0", "end")
        with open(filepath, "r", encoding="utf-8") as f:
            text_widget.insert("1.0", f.read())


def handle_tree_open(x):
    print(x)
    current_dir = file_tree.focus()
    current_sub_dir = file_tree.get_children(current_dir)
    print(current_dir)
    print(current_sub_dir)
    if len(os.listdir(current_dir)):
        for sub in current_sub_dir:
            file_tree.delete(sub)
    if os.path.isdir(current_dir):
        for sub in os.listdir(current_dir):
            sub_child = Path(current_dir)/sub
            file_tree.insert(str(Path(current_dir)), "end", str(sub_child), text=sub)
            if sub_child.is_dir():
                file_tree.insert(str(sub_child), "end", text="<empty>")


def handle_tree_select(x):
    file_tree.focus_get().bind("<Double-1>", handle_open_file)


def show_remote_dialog():
    remote_dialog(root, param_holder, ssh_wrapper, file_tree, text_widget)


def handle_window_close():
    stop_file_thread()
    ssh_wrapper.close()
    root.destroy()


def track_cursor_enter(e):
    root.config(cursor="sb_h_double_arrow")


def track_cursor_leave(e):
    root.config(cursor="arrow")


def resize_widget(e):
    root.config(cursor="sb_h_double_arrow")
    # print(file_tree.column("#0").get("width") + e.x)
    file_tree.grid_remove()
    file_tree.column("#0", width=file_tree.column("#0").get("width") + e.x)
    # print(file_tree.column("#0"))
    file_tree.grid(column=0, row=0, sticky=(N, S, E, W))


def redraw_widget(e):
    print("stop")
    root.config(cursor="arrow")
    # file_tree.grid_forget()
    # file_tree.column("#0", width=200)
    # file_tree.grid(column=0, row=0, sticky=(N, S, E, W))

    # children = file_tree.get_children()
    # for child in children:
    #     file_tree.detach(child)
    #
    #
    #
    # n_file_tree = ttk.Treeview(file_list_frame)
    # for child in children:
    #     n_file_tree.move(child, "", "end")
    # file_tree.destroy()
    # n_file_tree.column("#0", width=file_list_width + e.x)
    # n_file_tree.grid(column=0, row=0, sticky=(N, S, E, W))


root = Tk()
root.title("Log Viewer")
root.minsize(1280, 800)
root.option_add("*tearOff", FALSE)
root.protocol("WM_DELETE_WINDOW", handle_window_close)

from icons import *

mainframe = ttk.Frame(root)
mainframe.grid(column=0, row=0, sticky=(N, S, E, W))
sep = ttk.Separator(mainframe, orient=VERTICAL)

menubar = Menu(root)
root["menu"] = menubar
menubar.add_command(label="download", image=ICON_DOWNLOAD)
menubar.add_command(label="setting", image=ICON_GEAR, command=show_remote_dialog)


file_list_frame = ttk.Frame(mainframe)

text_frame = ttk.Frame(mainframe)
file_tree = ttk.Treeview(file_list_frame)
file_tree.column("#0", width=500, stretch=True)

text_widget = Text(text_frame)
file_list_scroll_y = Scrollbar(file_list_frame, orient=VERTICAL, command=file_tree.yview)
text_scroll = Scrollbar(text_frame, orient=VERTICAL, command=text_widget.yview)

file_tree["show"] = "tree"
file_tree["yscrollcommand"] = file_list_scroll_y.set
text_widget["yscrollcommand"] = text_scroll.set
text_widget.bind("<Control-a>", lambda x: text_widget.tag_add("sel", "1.0"))
text_widget.bind("<Control-A>", lambda x: text_widget.tag_add("sel", "1.0"))
text_widget.tag_config("sel", background="grey")

sep.bind("<Enter>", track_cursor_enter)
sep.bind("<Leave>", track_cursor_leave)
sep.bind("<B1-Motion>", resize_widget)
sep.bind("<ButtonRelease>", redraw_widget)

for d in home_dir:
    file_tree.insert("", "end", str(Path("/home/eason")/d), text=d)
    if (Path("/home/eason")/d).is_dir():
        file_tree.insert(str(Path("/home/eason")/d), "end", text="<empty>")


# file_tree.bind("<<TreeviewOpen>>", handle_tree_open)
# file_tree.bind("<<TreeviewSelect>>", handle_tree_select)


file_list_frame.grid(column=0, row=0, sticky=(N, S, E, W))
sep.grid(column=1, row=0, sticky=(N, S))
text_frame.grid(column=2, row=0, sticky=(N, S, E, W))

file_list_scroll_y.grid(column=1, row=0, sticky=(N, S, E, W))
text_scroll.grid(column=1, row=0, sticky=(N, S, E, W))

# file_list_widget.grid(column=0, row=0, sticky=(N, S, E, W))
text_widget.grid(column=0, row=0, sticky=(N, S, E, W))
file_tree.grid(column=0, row=0, sticky=(N, S, E, W))


root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

mainframe.rowconfigure(0, weight=1)
# mainframe.columnconfigure(0, weight=3)
# mainframe.columnconfigure(1, weight=0)
mainframe.columnconfigure(2, weight=1)

file_list_frame.rowconfigure(0, weight=1)
file_list_frame.columnconfigure(0, weight=1)
text_frame.rowconfigure(0, weight=1)
text_frame.columnconfigure(0, weight=1)

ttk.Style().configure("Treeview", rowheight=40)


if __name__ == '__main__':
    root.mainloop()
