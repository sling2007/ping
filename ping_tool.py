import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import platform


class PingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ping_tool")
        self.process = None
        self.running = False

        # --- 界面布局 ---
        # 地址输入栏
        self.frame_top = tk.Frame(root)
        self.frame_top.pack(pady=10)

        tk.Label(self.frame_top, text="Address:", width=10).grid(row=0, column=0)
        self.entry_addr = tk.Entry(self.frame_top, width=40)
        self.entry_addr.insert(0, "www.whieda.com")
        self.entry_addr.grid(row=0, column=1)

        # 按钮栏
        self.frame_btns = tk.Frame(root)
        self.frame_btns.pack(pady=5)

        self.btn_start = tk.Button(self.frame_btns, text="start", width=10, command=self.start_ping)
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_stop = tk.Button(self.frame_btns, text="stop", width=10, command=self.stop_ping, state=tk.DISABLED)
        self.btn_stop.grid(row=0, column=1, padx=5)

        # 日志输出框
        self.log_area = scrolledtext.ScrolledText(root, width=70, height=25)
        self.log_area.pack(padx=10, pady=10)

    def start_ping(self):
        addr = self.entry_addr.get().strip()
        if not addr:
            return

        self.running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)  # 清空旧日志

        # 在新线程中运行 ping，避免界面卡死
        self.thread = threading.Thread(target=self.run_ping, args=(addr,), daemon=True)
        self.thread.start()

    def run_ping(self, addr):
        # 根据系统判断参数，Windows用 -t，Linux/Mac用 -i
        param = "-t" if platform.system().lower() == "windows" else ""
        command = f"ping {addr} {param}"

        self.log_area.insert(tk.END, f"执行命令: {command}\n\n")

        # 启动子进程
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            bufsize=1
        )

        # 实时读取输出
        for line in iter(self.process.stdout.readline, ''):
            if not self.running:
                break
            self.log_area.insert(tk.END, line)
            self.log_area.see(tk.END)  # 滚动到底部

        self.process.stdout.close()

    def stop_ping(self):
        self.running = False
        if self.process:
            # 终止子进程
            subprocess.Popen("TASKKILL /F /PID {pid} /T".format(pid=self.process.pid), shell=True)

        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.log_area.insert(tk.END, "\n--- 已停止 ---\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = PingApp(root)
    root.mainloop()