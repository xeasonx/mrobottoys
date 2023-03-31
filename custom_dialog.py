import paramiko.client

from pathlib import Path
from threading import Thread
from tkinter import *
from tkinter import ttk


file_thread = []


class ParamHolder:
    def __init__(self):
        self.params = {}

    def set_param(self, param_name, param_val):
        if param_name not in self.params:
            self.params[param_name] = param_val

    def get_param(self, param_name):
        return self.params[param_name]


class SSHWrapper:
    def __init__(self):
        self.option = None
        self.ssh_client = None
        self.sftp_client = None
        self.remote_home = None

    def connect(self, option):
        self.ssh_client = paramiko.client.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy)
        try:
            self.ssh_client.connect(option["host"], option["port"], option["username"], option["password"], timeout=30)
            self.sftp_client = self.ssh_client.open_sftp()
            self.sftp_client.sock.settimeout(30)
            self.remote_home = self.sftp_client.normalize(".")
            return True
        except Exception as e:
            print(e)
            return False

    def is_dir(self, p):
        try:
            self.sftp_client.listdir(p)
        except FileNotFoundError:
            return False
        except PermissionError:
            return False
        else:
            return True

    def close(self):
        if self.sftp_client is not None:
            self.sftp_client.close()
            self.sftp_client.close()
            print("close ssh connection")


class RemoteFileThread(Thread):
    def __init__(self, remote_filepath, sftp_instance, text_widget):
        Thread.__init__(self)
        self.filepath = remote_filepath
        self.sftp = sftp_instance
        self.text_widget = text_widget
        self.is_stop = False
        self.buffer = 1024

    def run(self) -> None:
        print(f"reading {self.filepath}")
        self.text_widget.delete("1.0", "end")
        try:
            f = self.sftp.open(self.filepath)
            while not self.is_stop:
                f.seek(f.tell())
                try:
                    bytes_read = f.read(self.buffer).decode("utf-8")
                    if len(bytes_read.strip()):
                        print(f"{len(bytes_read)} read")
                        self.text_widget.insert("end", bytes_read)
                        self.text_widget.see("end")
                except UnicodeDecodeError:
                    print("decode failed")
                    break
            f.close()
        except PermissionError:
            print("permission denied")
        except Exception:
            print("unknown error")
        finally:
            f.close()


def stop_file_thread():
    if len(file_thread):
        print("stop reading thread")
        file_thread[0].is_stop = True
        file_thread[0].join()


def update_tree(tree_widget, text_widget, ssh_wrapper: SSHWrapper):
    def handle_remote_open_file(x):
        stop_file_thread()
        remote_filepath = tree_widget.focus()
        if ssh_wrapper.is_dir(remote_filepath):
            handle_remote_tree_open(x)
        else:
            remote_file_thread = RemoteFileThread(remote_filepath, ssh_wrapper.sftp_client, text_widget)
            if len(file_thread):
                file_thread[0].is_stop = True
                file_thread[0].join()
                file_thread.clear()
            file_thread.append(remote_file_thread)
            remote_file_thread.start()

    def handle_remote_tree_open(x):
        stop_file_thread()
        current_dir = tree_widget.focus()
        current_sub_dir = tree_widget.get_children(current_dir)
        print(current_dir)
        print(current_sub_dir)
        if len(ssh_wrapper.sftp_client.listdir(current_dir)):
            for sub in current_sub_dir:
                tree_widget.delete(sub)
        if ssh_wrapper.is_dir(current_dir):
            dir_list = ssh_wrapper.sftp_client.listdir(current_dir)
            for sub in sorted(dir_list):
                sub_child = Path(current_dir) / sub
                tree_widget.insert(str(Path(current_dir)), "end", str(sub_child), text=sub)
                if ssh_wrapper.is_dir(str(sub_child)):
                    tree_widget.insert(str(sub_child), "end", text="<empty>")
                    
    def handle_context_menu(e):
        menu = Menu(tree_widget)
        menu.add_command(label="toggle")
        menu.add_command(label="open")
        menu.add_command(label="open in new window")
        menu.post(e.x_root, e.y_root)

    def handle_remote_tree_select(x):
        tree_widget.focus_get().bind("<Double-1>", handle_remote_open_file)
        tree_widget.focus_get().bind("<3>", handle_context_menu)

    stop_file_thread()
    for child in tree_widget.get_children():
        tree_widget.delete(child)
    dir_list = ssh_wrapper.sftp_client.listdir(ssh_wrapper.remote_home)
    for d in sorted(dir_list):
        target_path = Path(ssh_wrapper.remote_home)/d
        tree_widget.insert("", "end", str(target_path), text=d)
        if ssh_wrapper.is_dir(str(target_path)):
            tree_widget.insert(str(target_path), "end", text="<empty>")

    tree_widget.bind("<<TreeviewOpen>>", handle_remote_tree_open)
    tree_widget.bind("<<TreeviewSelect>>", handle_remote_tree_select)


def remote_dialog(parent, param_holder: ParamHolder, ssh_wrapper: SSHWrapper, tree_widget, text_widget):
    def apply():
        print(param_holder.params["host"].get())
        ssh_wrapper.close()
        ssh_opt = {
            "host": param_holder.params["host"].get(),
            "port": param_holder.params["port"].get(),
            "username": param_holder.params["username"].get(),
            "password": param_holder.params["password"].get()
        }
        is_connect = ssh_wrapper.connect(ssh_opt)
        if is_connect:
            dialog.grab_release()
            dialog.destroy()
            update_tree(tree_widget, text_widget, ssh_wrapper)
        else:
            print("connection error")

    def dismiss():
        dialog.grab_release()
        dialog.destroy()

    dialog = Toplevel(parent)
    param_holder.set_param("host", StringVar(value="192.168.3.51"))
    param_holder.set_param("port", IntVar(value=22))
    param_holder.set_param("username", StringVar(value="mrobot"))
    param_holder.set_param("password", StringVar(value="mrobot()"))
    label_host = ttk.Label(dialog, text="Host:")
    label_port = ttk.Label(dialog, text="Port:")
    label_username = ttk.Label(dialog, text="Username:")
    label_password = ttk.Label(dialog, text="password:")
    host_entry = ttk.Entry(dialog, textvariable=param_holder.get_param("host"))
    port_entry = ttk.Entry(dialog, textvariable=param_holder.get_param("port"))
    username_entry = ttk.Entry(dialog, textvariable=param_holder.get_param("username"))
    password_entry = ttk.Entry(dialog, textvariable=param_holder.get_param("password"))
    button_ok = ttk.Button(dialog, text="OK", command=apply)
    button_cancel = ttk.Button(dialog, text="Cancel", command=dismiss)

    label_host.grid(column=0, row=0, sticky=(E,))
    label_port.grid(column=0, row=1, sticky=(E,))
    label_username.grid(column=0, row=2, sticky=(E,))
    label_password.grid(column=0, row=3, sticky=(E,))

    host_entry.grid(column=1, row=0, columnspan=3, sticky=(E, W))
    port_entry.grid(column=1, row=1, columnspan=3, sticky=(E, W))
    username_entry.grid(column=1, row=2, columnspan=3, sticky=(E, W))
    password_entry.grid(column=1, row=3, columnspan=3, sticky=(E, W))
    button_ok.grid(column=2, row=4)
    button_cancel.grid(column=3, row=4)

    dialog.transient(parent)
    dialog.wait_visibility()
    dialog.grab_set()
    dialog.wait_window()
