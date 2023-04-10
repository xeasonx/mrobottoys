import paramiko.client
import traceback
import threading

from pathlib import Path
from threading import Thread, Event, Lock
from tkinter import *
from tkinter import ttk


file_thread = {}

context_menu = None


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
        self.is_connectting = False
        
    def set_opt(self, option):
        self.option = option

    def connect(self, option):
        self.ssh_client = paramiko.client.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy)
        try:
            self.is_connectting = True
            self.ssh_client.connect(option["host"], option["port"], option["username"], option["password"], timeout=30)
            self.sftp_client = self.ssh_client.open_sftp()
            self.sftp_client.sock.settimeout(30)
            self.remote_home = self.sftp_client.normalize(".")
            self.is_connectting = False
            return True
        except Exception as e:
            print(e)
            self.close()
            self.ssh_client = None
            self.sftp_client = None
            return False

    def is_dir(self, p):
        try:
            self.sftp_client.listdir(Path(p).as_posix())
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
            

class RemoteCompress(Thread):
    def __init__(self, ssh_option, cwd, filename):
        Thread.__init__(self)
        self.ssh_option = ssh_option
        self.cwd = cwd
        self.filename = filename
        self.is_done = False
        self.is_success = False
        self.ssh_client = None
        self.sftp_client = None
        self.is_connectting = False
        self.stdout = None
        self.stderr = None
        
    def connect(self, option):
        self.ssh_client = paramiko.client.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy)
        try:
            self.is_connectting = True
            self.ssh_client.connect(option["host"], option["port"], option["username"], option["password"], timeout=30)
            self.sftp_client = self.ssh_client.open_sftp()
            self.sftp_client.sock.settimeout(30)
            self.is_connectting = False
            return True
        except Exception as e:
            print(e)
            return False

    def close(self):
        if self.sftp_client is not None:
            self.sftp_client.close()
            self.sftp_client.close()
            print("close ssh connection")
            
    def remove(self):
        cmd = f"cd {self.cwd} && rm {self.filename}"
        print(cmd)
        self.ssh_client.exec_command(cmd)
        
    def run(self):
        if self.connect(self.ssh_option):
            cmd = f"cd {self.cwd} && tar -cf {self.filename} *"
            print(cmd)
            _, self.stdout, self.stderr = self.ssh_client.exec_command(cmd)
            self.is_done = True
            # if len(err.read()):
            #     self.is_success = False
            #     print("compress failed")
            # else:
            #     self.is_success = True
            #     print("compress success")
        


class RemoteFileThread(Thread):
    def __init__(self, remote_filepath, ssh_instance, text_widget):
        Thread.__init__(self)
        self.filepath = remote_filepath
        self.ssh_instance = ssh_instance
        self.ssh_client = None
        self.sftp_channel = None
        self.f = None
        self.text_widget = text_widget
        self.buffer = 2048
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.pause_event.set()
        
    def _open_sftp(self) -> bool:
        if self.ssh_instance.option is not None:
            self.ssh_client = paramiko.client.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy)
        try:
            self.ssh_client.connect(
                self.ssh_instance.option["host"], 
                self.ssh_instance.option["port"], 
                self.ssh_instance.option["username"], 
                self.ssh_instance.option["password"], 
                timeout=30
            )
            self.sftp_channel = self.ssh_client.open_sftp()
            self.sftp_channel.sock.settimeout(30)
            return True
        except Exception as e:
            print(e)
            self._close_sftp()
            return False
        
    def _close_sftp(self):
        if self.sftp_channel is not None:
            self.sftp_channel.close()
            print("sftp channel closed")
        if self.ssh_client is not None:
            self.ssh_client.close()
            print("ssh client closed")
            
    def reopen(self, filepath):
        self.f.close()
        self.filepath = filepath
        self.text_widget.delete("1.0", "end")
        try:
            self.f = self.sftp_channel.open(filepath, bufsize=1)
            print(f"reopen {filepath} success")
        except Exception:
            self.text_widget.insert("end", f"reopen {filepath} failed")
            self.f.close()
        
    def pause(self):
        self.pause_event.clear()
        print("pause")
    
    def resume(self):
        self.pause_event.set()
        print("resume")
        
    def stop(self):
        self.stop_event.set()
        print("stop")

    def run(self) -> None:
        if not self._open_sftp():
            print("sftp channel open failed")
            self.text_widget.insert("end", "sftp channel open failed")
            return
        print(f"reading {self.filepath}")
        self.text_widget.delete("1.0", "end")
        self.f = self.sftp_channel.open(self.filepath, bufsize=1)
        
        while True:
            self.pause_event.wait()
            if self.stop_event.is_set():
                break
            
            self.f.seek(self.f.tell())
            
            try:
                bytes_read = self.f.read(self.buffer).decode("utf-8", "ignore")
                if len(bytes_read.strip()):
                    self.text_widget.insert("end", bytes_read)
                    self.text_widget.see("end")
            except PermissionError:
                self.text_widget.insert("end", "permission denied")
                print("permission denied")
                self.pause()
            except UnicodeDecodeError:
                self.text_widget.insert("end", "decode failed")
                print("decode failed")
                self.pause()
            except Exception as e:
                print(e)
                print(traceback.print_exc())
                print("unknown error")
                self.text_widget.insert("end", "unknown error")
                self.pause()
        self._close_sftp()


def stop_file_thread():
    for t in file_thread.values():
        if t.is_alive():
            print(f"stop reading {t.filepath}")
            t.resume()
            t.stop()
            t.join()


def update_tree(tree_widget, text_widget, ssh_wrapper: SSHWrapper, context_menu):
    def handle_remote_open_file(x):
        # stop_file_thread()
        remote_filepath = tree_widget.focus()
        if ssh_wrapper.is_dir(remote_filepath):
            handle_remote_tree_open(x)
        else:
            if 0 not in file_thread:
                remote_file_thread = RemoteFileThread(remote_filepath, ssh_wrapper, text_widget)
                if len(file_thread):
                    file_thread[0].resume()
                    file_thread[0].stop()
                    file_thread[0].join()
                file_thread[0] = remote_file_thread
                remote_file_thread.start()
            else:
                print("reopen text in main window")
                file_thread[0].pause()
                file_thread[0].reopen(remote_filepath)
                file_thread[0].resume()

    def handle_remote_tree_open(x):
        # stop_file_thread()
        current_dir = tree_widget.focus()
        current_sub_dir = tree_widget.get_children(current_dir)
        # print(current_dir)
        # print(current_sub_dir)
        if len(ssh_wrapper.sftp_client.listdir(current_dir)):
            for sub in current_sub_dir:
                tree_widget.delete(sub)
        if ssh_wrapper.is_dir(current_dir):
            dir_list = ssh_wrapper.sftp_client.listdir(current_dir)
            for sub in sorted(dir_list):
                sub_child = (Path(current_dir)/sub).as_posix()
                tree_widget.insert(current_dir, "end", sub_child, text=sub)
                if ssh_wrapper.is_dir(sub_child):
                    tree_widget.insert(sub_child, "end", text="<empty>")
                    
    def handle_context_menu(e):
        context_menu.unpost()
        context_menu.post(e.x_root, e.y_root)


    def handle_remote_tree_select(x):
        tree_widget.focus_get().bind("<Double-1>", handle_remote_open_file)
        tree_widget.focus_get().bind("<3>", handle_context_menu)

    def handle_right_click(e):
        print(e)
        handle_context_menu(e)

    stop_file_thread()
    for child in tree_widget.get_children():
        tree_widget.delete(child)
    dir_list = ssh_wrapper.sftp_client.listdir(ssh_wrapper.remote_home)
    for d in sorted(dir_list):
        target_path = (Path(ssh_wrapper.remote_home)/d).as_posix()
        tree_widget.insert("", "end", target_path, text=d)
        if ssh_wrapper.is_dir(target_path):
            tree_widget.insert(target_path, "end", text="<empty>")
    tree_widget.bind("<<TreeviewOpen>>", handle_remote_tree_open)
    tree_widget.bind("<<TreeviewSelect>>", handle_remote_tree_select)


def remote_dialog(parent, param_holder: ParamHolder, ssh_wrapper: SSHWrapper, tree_widget, text_widget, context_menu):
    def apply():
        t = Thread(target=apply_thread)
        t.start()
    
    def apply_thread():
        print(param_holder.params["host"].get())
        ssh_wrapper.close()
        ssh_opt = {
            "host": param_holder.params["host"].get(),
            "port": param_holder.params["port"].get(),
            "username": param_holder.params["username"].get(),
            "password": param_holder.params["password"].get()
        }
        status_var.set("connecting...")
        button_ok.state(["disabled"])
        button_cancel.state(["disabled"])
        ssh_wrapper.set_opt(ssh_opt)
        is_connect = ssh_wrapper.connect(ssh_opt)
        if is_connect:
            dialog.grab_release()
            dialog.destroy()
            update_tree(tree_widget, text_widget, ssh_wrapper, context_menu)
        else:
            status_result
            status_var.set("connection error")
            print("connection error")
        button_ok.state(["!disabled"])
        button_cancel.state(["!disabled"])

    def dismiss():
        dialog.grab_release()
        dialog.destroy()

    dialog = Toplevel(parent)
    status_var = StringVar(value="null")
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
    
    label_status = ttk.Label(dialog, text="Status:")
    status_result = ttk.Label(dialog, textvariable=status_var)
    
    button_ok = ttk.Button(dialog, text="OK", command=apply)
    button_cancel = ttk.Button(dialog, text="Cancel", command=dismiss)

    label_host.grid(column=0, row=0, sticky=(E,))
    label_port.grid(column=0, row=1, sticky=(E,))
    label_username.grid(column=0, row=2, sticky=(E,))
    label_password.grid(column=0, row=3, sticky=(E,))
    label_status.grid(column=0, row=4, sticky=(E,))

    host_entry.grid(column=1, row=0, columnspan=3, sticky=(E, W))
    port_entry.grid(column=1, row=1, columnspan=3, sticky=(E, W))
    username_entry.grid(column=1, row=2, columnspan=3, sticky=(E, W))
    password_entry.grid(column=1, row=3, columnspan=3, sticky=(E, W))
    status_result.grid(column=1, row=4, columnspan=3, sticky=(E, W))
    
    button_ok.grid(column=2, row=5)
    button_cancel.grid(column=3, row=5)

    dialog.transient(parent)
    dialog.wait_visibility()
    dialog.grab_set()
    dialog.wait_window()


def create_log_window(parent, filepath, ssh_wrapper, context_menu):
    def handle_log_window_close():
        print(f"stop reading {filepath}")
        file_thread[window_id].resume()
        file_thread[window_id].stop()
        file_thread[window_id].join()
        del file_thread[window_id]
        log_window.grab_release()
        log_window.destroy()
        
    def pause_reading():
        if is_reading_pause.get():
            print("pause")
            file_thread[window_id].pause()
        else:
            print("resume")
            file_thread[window_id].resume()

    # stop_file_thread()
    context_menu.unpost()

    is_reading_pause = BooleanVar()
    log_window = Toplevel(parent)
    log_window.title(filepath)
    window_id = log_window.winfo_id()
    print(log_window.winfo_id())
    
    action_pause = ttk.Checkbutton(log_window, text="pause", command=pause_reading, variable=is_reading_pause, onvalue=True, offvalue=False)
    action_pause.grid(column=0, row=0, sticky=(N, S, E, W))
    
    log_window.columnconfigure(0, weight=1)
    log_window.rowconfigure(1, weight=1)

    log_window.protocol("WM_DELETE_WINDOW", handle_log_window_close)

    log_text = Text(log_window)
    vscroll = Scrollbar(log_window, orient=VERTICAL, command=log_text.yview)
    log_text["yscrollcommand"] = vscroll.set

    log_text.grid(column=0, row=1, sticky=(N, S, E, W))
    vscroll.grid(column=1, row=1, sticky=(N, S))
    log_text.columnconfigure(0, weight=1)
    log_text.rowconfigure(0, weight=1)
    remote_file_thread = RemoteFileThread(filepath, ssh_wrapper, log_text)
    file_thread[window_id] =remote_file_thread
    remote_file_thread.start()
    # log_window.transient(parent)
    # log_window.wait_visibility()
    # log_window.grab_set()
    # log_window.wait_window()
