import os
import datetime
import threading
import tkinter.filedialog

from pathlib import Path
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from custom_dialog import remote_dialog, ParamHolder, SSHWrapper, RemoteCompress, stop_file_thread, create_log_window, file_thread

home_dir = os.listdir(Path().home())
param_holder = ParamHolder()
ssh_wrapper = SSHWrapper()
is_transfer_start = False
transfered_bytes = 0
total_transfered_bytes = 0
compress_thread = None


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
    remote_dialog(root, param_holder, ssh_wrapper, file_tree, text_widget, context_menu)


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


def handle_mouse_click(e):
    # from custom_dialog import context_menu
    if context_menu is not None:
        context_menu.unpost()
        
        
def pause_reading():
    if is_reading_pause.get():
        print("pause")
        file_thread[0].pause()
    else:
        print("resume")
        file_thread[0].resume()
        

def transfer_remote_filepath():
    global is_transfer_start, transfered_bytes, total_transfered_bytes
    
    def update_progress(bytes_trans, bytes_total):
        global transfered_bytes, total_transfered_bytes
        
        transfered_bytes = bytes_trans
        total_transfered_bytes = bytes_total
        
    def step():
        global transfered_bytes, total_transfered_bytes, compress_thread
        
        # print(f"step: {transfered_bytes} / {total_transfered_bytes}")
        if total_transfered_bytes != 0 and total_transfered_bytes == transfered_bytes:
            transfer_percent_val.set("100%")
            transfer_progress["value"] = 100
            print("transfer done")
            if compress_thread is not None:
                compress_thread.remove()
                compress_thread.join()
                compress_thread = None
            return
        
        try:
            p = int(transfered_bytes / total_transfered_bytes * 100)
            transfer_percent_val.set(f"{p}%")
            transfer_progress["value"] = p
            transfer_window.after(500, step)
        except ZeroDivisionError:
            pass
        

        transfer_window.after(500, step)
    
    
    def start_file(remote_filepath=None, local_filepath=None):
        global is_transfer_start, transfered_bytes, total_transfered_bytes
        
        if total_transfered_bytes != 0 and total_transfered_bytes == transfered_bytes:
            return
        
        if not is_transfer_start:
            is_transfer_start = True
            if remote_filepath is None:
                t = threading.Thread(target=ssh_wrapper.sftp_client.get, args=(remote_path, save_path, update_progress))
            else:
                print(remote_filepath, local_filepath)

                t = threading.Thread(target=ssh_wrapper.sftp_client.get, args=(remote_filepath, local_filepath, update_progress))
            t.start()
        transfer_window.after(500, step)
        
    is_transfer_start = False
    transfered_bytes = 0
    total_transfered_bytes = 0
    transfer_percent_val = StringVar(value="0%")
    save_path = tkinter.filedialog.askdirectory()
    remote_path = file_tree.focus()
    
    def start_dir():
        global is_transfer_start, compress_thread
        
        tar_name = f"{Path(remote_path).parts[-1]}_{file_suffix}.tar.gz"
        
        if not is_transfer_start:
            is_transfer_start = True
            ssh_opt = {
                "host": param_holder.params["host"].get(),
                "port": param_holder.params["port"].get(),
                "username": param_holder.params["username"].get(),
                "password": param_holder.params["password"].get()
            }
            compress_thread = RemoteCompress(ssh_opt, Path(remote_path).as_posix(), tar_name)
            compress_thread.start()
        else:
            if compress_thread.stderr is not None:
                err = compress_thread.stderr.read()
                print(err)
                if not len(err) or b"file changed" in err:
                    is_transfer_start = False
                    start_file((Path(remote_path)/tar_name).as_posix(), (Path(save_path)/tar_name).resolve())
                    return
                else:
                    transfer_percent_val.set("-1")
                    return
        transfer_window.after(500, start_dir)
            
    
    file_suffix = f"{datetime.datetime.now():%Y%m%d%H%M%S}"
    transfer_window = Toplevel(root)
    transfer_window.title("Transfer")
    file_label_from = ttk.Label(transfer_window, text="Source:")
    file_label_to = ttk.Label(transfer_window, text="Destination:")
    file_src = ttk.Label(transfer_window, text=remote_path)
    file_dst = ttk.Label(transfer_window, text=save_path)
    transfer_progress = ttk.Progressbar(transfer_window, orient="horizontal", mode="determinate", maximum=100)
    transfer_percent = ttk.Label(transfer_window, textvariable=transfer_percent_val)
    
    file_label_from.grid(column=0, row=0, sticky=(E,))
    file_src.grid(column=1, row=0, columnspan=4, sticky=(E, W))
    file_label_to.grid(column=0, row=1, sticky=(E,))
    file_dst.grid(column=1, row=1, columnspan=4, sticky=(E, W))
    transfer_progress.grid(column=0, row=2, columnspan=4, sticky=(E, W))
    transfer_percent.grid(column=45, row=2, sticky=(E, W))
    
    if ssh_wrapper.is_dir(remote_path):
        transfer_window.after(500, start_dir)
    else:
        file_name = Path(remote_path).parts[-1]
        save_path = (Path(save_path)/file_name).resolve()
        print(f"transfer {remote_path} to {save_path}")
        transfer_window.after(500, start_file)
    
    transfer_window.transient(root)
    transfer_window.wait_visibility()
    transfer_window.grab_set()
    transfer_window.wait_window()


root = Tk()
root.title("Log Viewer")
root.minsize(1280, 800)
root.option_add("*tearOff", FALSE)
root.protocol("WM_DELETE_WINDOW", handle_window_close)
root.bind("<ButtonPress-1>", handle_mouse_click)

from icons import *

mainframe = ttk.Frame(root)
mainframe.grid(column=0, row=1, sticky=(N, S, E, W))
is_reading_pause = BooleanVar()

# sep = ttk.Separator(mainframe, orient=VERTICAL)

# menubar = Menu(root)
# root["menu"] = menubar
# menubar.add_command(label="download", image=ICON_DOWNLOAD)
# menubar.add_command(label="setting", image=ICON_GEAR, command=show_remote_dialog)

action_frame = Frame(root)
action_setting = Button(action_frame, image=ICON_GEAR, width=32, height=32, command=show_remote_dialog)
action_pause = ttk.Checkbutton(action_frame, text="pause", command=pause_reading, variable=is_reading_pause, onvalue=True, offvalue=False)
action_setting.grid(column=0, row=0, sticky=(N, S, E, W))
action_pause.grid(column=1, row=0, sticky=(N, S, E, W))

file_list_frame = ttk.Frame(mainframe)

text_frame = ttk.Frame(mainframe)
file_tree = ttk.Treeview(file_list_frame)
file_tree.column("#0", stretch=True)

context_menu = Menu(file_tree)
context_menu.add_command(label="open in new window", command=lambda: create_log_window(root, file_tree.focus(), ssh_wrapper, context_menu))
context_menu.add_command(label="download", command=transfer_remote_filepath)

text_widget = Text(text_frame)
file_list_scroll_y = Scrollbar(file_list_frame, orient=VERTICAL, command=file_tree.yview)
text_scroll = Scrollbar(text_frame, orient=VERTICAL, command=text_widget.yview)

file_tree["show"] = "tree"
file_tree["yscrollcommand"] = file_list_scroll_y.set
text_widget["yscrollcommand"] = text_scroll.set
text_widget.bind("<Control-a>", lambda x: text_widget.tag_add("sel", "1.0"))
text_widget.bind("<Control-A>", lambda x: text_widget.tag_add("sel", "1.0"))
text_widget.tag_config("sel", background="grey")

# sep.bind("<Enter>", track_cursor_enter)
# sep.bind("<Leave>", track_cursor_leave)
# sep.bind("<B1-Motion>", resize_widget)
# sep.bind("<ButtonRelease>", redraw_widget)

for d in home_dir:
    file_tree.insert("", "end", str(Path.home()/d), text=d)
    if (Path.home()/d).is_dir():
        file_tree.insert(str(Path.home()/d), "end", text="<empty>")

# file_tree.bind("<<TreeviewOpen>>", handle_tree_open)
# file_tree.bind("<<TreeviewSelect>>", handle_tree_select)
file_list_frame.grid(column=0, row=0, sticky=(N, S, E, W))
# sep.grid(column=1, row=0, sticky=(N, S))
text_frame.grid(column=1, row=0, sticky=(N, S, E, W))

file_list_scroll_y.grid(column=1, row=0, sticky=(N, S, E, W))
text_scroll.grid(column=1, row=0, sticky=(N, S, E, W))

# file_list_widget.grid(column=0, row=0, sticky=(N, S, E, W))
text_widget.grid(column=0, row=0, sticky=(N, S, E, W))
file_tree.grid(column=0, row=0, sticky=(N, S, E, W))
action_frame.grid(column=0, row=0, sticky=(E, W))


root.rowconfigure(1, weight=1)
root.columnconfigure(0, weight=1)

mainframe.rowconfigure(0, weight=1)
mainframe.columnconfigure(0, weight=2)
mainframe.columnconfigure(1, weight=3)
# mainframe.columnconfigure(2, weight=1)

file_list_frame.rowconfigure(0, weight=1)
file_list_frame.columnconfigure(0, weight=1)
text_frame.rowconfigure(0, weight=1)
text_frame.columnconfigure(0, weight=1)

ttk.Style().configure("Treeview", rowheight=40)


if __name__ == '__main__':
    print(root.winfo_id())
    root.mainloop()
