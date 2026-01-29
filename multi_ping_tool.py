import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import platform


class MultiPingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ping tool")

        # 预设的6个地址
        self.default_addresses = [
            "www.whieda.org", "www.whieda.eu", "ht.whieda.org",
            "weihu.whieda.org", "www.baidu.com", "8.8.8.8"
        ]

        self.processes = []  # 存储当前运行的子进程
        self.running_count = 0  # 记录正在运行的线程数量
        self.running = False

        # --- 顶部全局控制栏 ---
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(pady=10, fill=tk.X)

        # 左侧 Start / Stop 按钮
        self.btn_frame = tk.Frame(self.top_frame)
        self.btn_frame.pack(side=tk.LEFT, padx=20)

        self.btn_start = tk.Button(self.btn_frame, text="start", width=12, command=self.start_all)
        self.btn_start.pack(side=tk.LEFT)

        self.btn_stop = tk.Button(self.btn_frame, text="stop", width=12, command=self.stop_all, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT)

        # 右侧 Default Num 参数设置
        self.param_frame = tk.Frame(self.top_frame, bd=1, relief=tk.SOLID)
        self.param_frame.pack(side=tk.RIGHT, padx=20)

        tk.Label(self.param_frame, text="default num:", width=12).pack(side=tk.LEFT)
        self.entry_num = tk.Entry(self.param_frame, width=10, justify='center')
        self.entry_num.insert(0, "20")  # 默认20次
        self.entry_num.pack(side=tk.LEFT, padx=5)

        # --- 6个Ping窗口的容器 (自适应布局) ---
        self.grid_frame = tk.Frame(root)
        self.grid_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        for i in range(2): self.grid_frame.columnconfigure(i, weight=1)
        for i in range(3): self.grid_frame.rowconfigure(i, weight=1)

        self.widgets = []
        for i in range(6):
            row = i // 2
            col = i % 2
            cell = self.create_ping_cell(self.grid_frame, self.default_addresses[i], row, col)
            self.widgets.append(cell)

        # 启动后自动开始执行
        self.root.after(500, self.start_all)

    def create_ping_cell(self, parent, default_addr, r, c):
        frame = tk.LabelFrame(parent, text=f"节点 {r * 2 + c + 1}", padx=5, pady=5)
        frame.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")

        addr_frame = tk.Frame(frame)
        addr_frame.pack(fill=tk.X)
        tk.Label(addr_frame, text="Address:").pack(side=tk.LEFT)
        entry = tk.Entry(addr_frame)
        entry.insert(0, default_addr)
        entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        log = scrolledtext.ScrolledText(frame, width=30, height=10, font=('Consolas', 9))
        log.pack(pady=5, fill=tk.BOTH, expand=True)

        return {"entry": entry, "log": log}

    def start_all(self):
        if self.running: return

        # 获取用户输入的次数
        try:
            self.current_max_count = int(self.entry_num.get().strip())
        except ValueError:
            self.current_max_count = 20  # 输入非法则默认为20

        self.running = True
        self.running_count = 6  # 初始为6个任务
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        self.processes = []
        for item in self.widgets:
            addr = item["entry"].get().strip()
            item["log"].delete(1.0, tk.END)
            # 开启线程
            thread = threading.Thread(
                target=self.run_single_ping,
                args=(addr, item["log"]),
                daemon=True
            )
            thread.start()

    def run_single_ping(self, addr, log_widget):
        count_param = "-n" if platform.system().lower() == "windows" else "-c"
        command = f"ping {addr} {count_param} {self.current_max_count}"

        log_widget.insert(tk.END, f"Ping {addr} ({self.current_max_count}次)...\n")

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

        # 任务结束后的回调
        self.check_finished()

    def check_finished(self):
        """每结束一个线程，计数减一，全部结束则恢复按钮状态"""
        self.running_count -= 1
        if self.running_count <= 0:
            self.running = False
            self.root.after(0, self.reset_buttons)

    def stop_all(self):
        self.running = False
        if platform.system().lower() == "windows":
            # 强制结束系统所有 ping 进程
            subprocess.Popen("TASKKILL /F /IM ping.exe /T", shell=True)

        self.reset_buttons()

    def reset_buttons(self):
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x850")
    # 设置主窗口自适应
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    app = MultiPingApp(root)
    root.mainloop()