import os
import tkinter.filedialog

from pathlib import Path
from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image

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
    root.destroy()


root = Tk()
root.title("Log Viewer")
root.minsize(1280, 800)
root.option_add("*tearOff", FALSE)
root.protocol("WM_DELETE_WINDOW", handle_window_close)

i = ImageTk.PhotoImage(Image.open("download.png"))
mainframe = ttk.Frame(root)
mainframe.grid(column=0, row=0, sticky=(N, S, E, W))

menubar = Menu(root)
root["menu"] = menubar
# menu_file = Menu(menubar)
# menu_edit = Menu(menubar)
# menubar.add_cascade(menu=menu_file, label='File')
# menubar.add_cascade(menu=menu_edit, label='Edit')
menubar.add_command(label="download", image=i, command=tkinter.filedialog.askdirectory)
menubar.add_command(label="connect", image=i, command=show_remote_dialog)
# menubar.add_command(label="download")


file_list_frame = ttk.Frame(mainframe)

text_frame = ttk.Frame(mainframe)
file_tree = ttk.Treeview(file_list_frame)

text_widget = Text(text_frame)
file_list_scroll_y = Scrollbar(file_list_frame, orient=VERTICAL, command=file_tree.yview)
text_scroll = Scrollbar(text_frame, orient=VERTICAL, command=text_widget.yview)

file_tree["yscrollcommand"] = file_list_scroll_y.set
text_widget["yscrollcommand"] = text_scroll.set
text_widget.bind("<Control-a>", lambda x: text_widget.tag_add("sel", "1.0", "end"))
text_widget.bind("<Control-A>", lambda x: text_widget.tag_add("sel", "1.0", "end"))
text_widget.tag_config("sel", background="gray")

# for d in home_dir:
#     file_tree.insert("", "end", str(Path("/home/eason")/d), text=d)
#     if (Path("/home/eason")/d).is_dir():
#         file_tree.insert(str(Path("/home/eason")/d), "end", text="<empty>")


# file_tree.bind("<<TreeviewOpen>>", handle_tree_open)
# file_tree.bind("<<TreeviewSelect>>", handle_tree_select)


# action_get = Button(root, image=i, default="active")
# action_get.grid(column=0, row=0)
# menubar.add_command()

file_list_frame.grid(column=0, row=0, sticky=(N, S, E, W))
text_frame.grid(column=1, row=0, sticky=(N, S, E, W))

file_list_scroll_y.grid(column=1, row=0, sticky=(N, S, E, W))
text_scroll.grid(column=1, row=0, sticky=(N, S, E, W))

# file_list_widget.grid(column=0, row=0, sticky=(N, S, E, W))
text_widget.grid(column=0, row=0, sticky=(N, S, E, W))
file_tree.grid(column=0, row=0, sticky=(N, S, E, W))


root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

mainframe.rowconfigure(0, weight=1)
mainframe.columnconfigure(0, weight=3)
mainframe.columnconfigure(1, weight=7)

file_list_frame.rowconfigure(0, weight=1)
file_list_frame.columnconfigure(0, weight=1)
text_frame.rowconfigure(0, weight=1)
text_frame.columnconfigure(0, weight=1)

ttk.Style().configure("Treeview", rowheight=40)


if __name__ == '__main__':
    root.mainloop()
