import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import platform


class MultiPingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Diagnosis Tool")

        # 前4个为Ping地址，后2个为Nslookup查询的目标
        self.ping_addresses = [
            "www.whieda.africa", "obs.whieda.org",
            "prod-hz.obs.ap-southeast-3.myhuaweicloud.com", "8.8.8.8"
        ]
        self.nslookup_targets = [
            "obs.whieda.org",
            "prod-hz.obs.ap-southeast-3.myhuaweicloud.com"
        ]

        self.processes = []
        self.running_count = 0
        self.running = False

        # --- 顶部控制栏 ---
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(pady=10, fill=tk.X)

        self.btn_frame = tk.Frame(self.top_frame)
        self.btn_frame.pack(side=tk.LEFT, padx=20)

        self.btn_start = tk.Button(self.btn_frame, text="start", width=12, command=self.start_all)
        self.btn_start.pack(side=tk.LEFT)

        self.btn_stop = tk.Button(self.btn_frame, text="stop", width=12, command=self.stop_all, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT)

        self.param_frame = tk.Frame(self.top_frame, bd=1, relief=tk.SOLID)
        self.param_frame.pack(side=tk.RIGHT, padx=20)

        tk.Label(self.param_frame, text="ping num:", width=12).pack(side=tk.LEFT)
        self.entry_num = tk.Entry(self.param_frame, width=10, justify='center')
        self.entry_num.insert(0, "20")
        self.entry_num.pack(side=tk.LEFT, padx=5)

        # --- 容器布局 (2列3行) ---
        self.grid_frame = tk.Frame(root)
        self.grid_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        for i in range(2): self.grid_frame.columnconfigure(i, weight=1)
        for i in range(3): self.grid_frame.rowconfigure(i, weight=1)

        self.widgets = []
        # 创建前4个 Ping 窗口
        for i in range(4):
            row, col = i // 2, i % 2
            cell = self.create_cell(self.grid_frame, "Ping", self.ping_addresses[i], row, col)
            self.widgets.append({"type": "ping", **cell})

        # 创建后2个 Nslookup 窗口
        for i in range(2):
            row, col = 2, i  # 最后一行
            cell = self.create_cell(self.grid_frame, "Nslookup", self.nslookup_targets[i], row, col)
            self.widgets.append({"type": "nslookup", **cell})

        self.root.after(500, self.start_all)

    def create_cell(self, parent, mode, default_addr, r, c):
        title = f"节点 {r * 2 + c + 1} ({mode})"
        frame = tk.LabelFrame(parent, text=title, padx=5, pady=5)
        frame.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")

        addr_frame = tk.Frame(frame)
        addr_frame.pack(fill=tk.X)
        tk.Label(addr_frame, text="Target:").pack(side=tk.LEFT)
        entry = tk.Entry(addr_frame)
        entry.insert(0, default_addr)
        entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        log = scrolledtext.ScrolledText(frame, width=30, height=8, font=('Consolas', 9))
        log.pack(pady=5, fill=tk.BOTH, expand=True)

        return {"entry": entry, "log": log}

    def start_all(self):
        if self.running: return

        try:
            self.current_max_count = int(self.entry_num.get().strip())
        except ValueError:
            self.current_max_count = 20

        self.running = True
        self.running_count = 6
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        self.processes = []
        for item in self.widgets:
            target = item["entry"].get().strip()
            item["log"].delete(1.0, tk.END)

            # 根据类型选择执行函数
            target_func = self.run_ping if item["type"] == "ping" else self.run_nslookup

            thread = threading.Thread(
                target=target_func,
                args=(target, item["log"]),
                daemon=True
            )
            thread.start()

    def run_ping(self, addr, log_widget):
        count_param = "-n" if platform.system().lower() == "windows" else "-c"
        command = f"ping {addr} {count_param} {self.current_max_count}"
        log_widget.insert(tk.END, f"执行 Ping: {addr} ({self.current_max_count}次)...\n")
        self.execute_command(command, log_widget)

    def run_nslookup(self, addr, log_widget):
        command = f"nslookup {addr}"
        log_widget.insert(tk.END, f"执行 Nslookup: {addr}...\n")
        self.execute_command(command, log_widget)

    def execute_command(self, command, log_widget):
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, shell=True, bufsize=1, encoding='gbk', errors='ignore'
        )
        self.processes.append(proc)

        for line in iter(proc.stdout.readline, ''):
            if not self.running: break
            log_widget.insert(tk.END, line)
            log_widget.see(tk.END)

        proc.stdout.close()
        proc.wait()
        self.check_finished()

    def check_finished(self):
        self.running_count -= 1
        if self.running_count <= 0:
            self.running = False
            self.root.after(0, self.reset_buttons)

    def stop_all(self):
        self.running = False
        if platform.system().lower() == "windows":
            subprocess.Popen("TASKKILL /F /IM ping.exe /T", shell=True)
            # nslookup 通常执行很快，但也可以尝试清理进程树
        self.reset_buttons()

    def reset_buttons(self):
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x900")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    app = MultiPingApp(root)
    root.mainloop()