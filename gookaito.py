import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import json
import time
import random
import threading
from typing import List, Optional
import os

class WalletSenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gookaito 批量发送工具")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        self.url = "https://www.gookaito.com/api/wallets"
        self.wallets = []
        self.proxy_list = []
        self.is_sending = False
        self.stop_sending = False
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/137.0.0.0 Safari/537.36"
        ]
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        title_label = ttk.Label(main_frame, text="Alpha还我血汗钱", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        ttk.Label(main_frame, text="钱包文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.wallet_file_var = tk.StringVar()
        wallet_entry = ttk.Entry(main_frame, textvariable=self.wallet_file_var, width=50)
        wallet_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))
        ttk.Button(main_frame, text="浏览", command=self.browse_wallet_file).grid(row=1, column=2, pady=5)
        
        proxy_frame = ttk.LabelFrame(main_frame, text="代理设置", padding="5")
        proxy_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        proxy_frame.columnconfigure(1, weight=1)
        
        self.use_proxy_var = tk.BooleanVar()
        ttk.Checkbutton(proxy_frame, text="使用代理", variable=self.use_proxy_var, 
                       command=self.toggle_proxy).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(proxy_frame, text="代理文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.proxy_file_var = tk.StringVar()
        self.proxy_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_file_var, width=50, state="disabled")
        self.proxy_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))
        self.proxy_browse_btn = ttk.Button(proxy_frame, text="浏览", command=self.browse_proxy_file, state="disabled")
        self.proxy_browse_btn.grid(row=1, column=2, pady=5)

        delay_frame = ttk.LabelFrame(main_frame, text="延迟设置", padding="5")
        delay_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(delay_frame, text="最小延迟(秒):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.min_delay_var = tk.StringVar(value="1")
        ttk.Entry(delay_frame, textvariable=self.min_delay_var, width=10).grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(delay_frame, text="最大延迟(秒):").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.max_delay_var = tk.StringVar(value="5")
        ttk.Entry(delay_frame, textvariable=self.max_delay_var, width=10).grid(row=0, column=3, pady=5, padx=5)
        
        status_frame = ttk.LabelFrame(main_frame, text="状态信息", padding="5")
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="钱包数量:").grid(row=0, column=0, sticky=tk.W)
        self.wallet_count_label = ttk.Label(status_frame, text="0")
        self.wallet_count_label.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(status_frame, text="代理数量:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.proxy_count_label = ttk.Label(status_frame, text="0")
        self.proxy_count_label.grid(row=0, column=3, sticky=tk.W, padx=10)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        self.load_btn = ttk.Button(button_frame, text="加载文件", command=self.load_files)
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        self.start_btn = ttk.Button(button_frame, text="开始发送", command=self.start_sending, state="disabled")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="停止发送", command=self.stop_sending_func, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        log_frame = ttk.LabelFrame(main_frame, text="发送日志", padding="5")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Button(log_frame, text="清除日志", command=self.clear_log).grid(row=1, column=0, pady=5)
    
    def toggle_proxy(self):
        """切换代理设置状态"""
        if self.use_proxy_var.get():
            self.proxy_entry.config(state="normal")
            self.proxy_browse_btn.config(state="normal")
        else:
            self.proxy_entry.config(state="disabled")
            self.proxy_browse_btn.config(state="disabled")
    
    def browse_wallet_file(self):
        """浏览钱包文件"""
        filename = filedialog.askopenfilename(
            title="选择钱包文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.wallet_file_var.set(filename)
    
    def browse_proxy_file(self):
        """浏览代理文件"""
        filename = filedialog.askopenfilename(
            title="选择代理文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.proxy_file_var.set(filename)
    
    def log_message(self, message):
        """添加日志消息"""
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """清除日志"""
        self.log_text.delete(1.0, tk.END)
    
    def load_files(self):
        """加载钱包和代理文件"""
        wallet_file = self.wallet_file_var.get()
        if not wallet_file:
            messagebox.showerror("错误", "请选择钱包文件")
            return
        
        try:
            with open(wallet_file, 'r', encoding='utf-8') as f:
                self.wallets = [line.strip() for line in f if line.strip()]
            self.wallet_count_label.config(text=str(len(self.wallets)))
            self.log_message(f"成功加载 {len(self.wallets)} 个钱包地址")
        except Exception as e:
            messagebox.showerror("错误", f"加载钱包文件失败: {e}")
            return
        
        self.proxy_list = []
        if self.use_proxy_var.get():
            proxy_file = self.proxy_file_var.get()
            if proxy_file and os.path.exists(proxy_file):
                try:
                    with open(proxy_file, 'r', encoding='utf-8') as f:
                        self.proxy_list = [line.strip() for line in f if line.strip()]
                    self.log_message(f"成功加载 {len(self.proxy_list)} 个代理")
                except Exception as e:
                    self.log_message(f"加载代理文件失败: {e}")
        
        self.proxy_count_label.config(text=str(len(self.proxy_list)))
        
        if self.wallets:
            self.start_btn.config(state="normal")
            self.log_message("文件加载完成，可以开始发送")
    
    def get_random_headers(self):
        """生成随机请求头"""
        return {
            "Host": "www.gookaito.com",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": '"Windows"',
            "User-Agent": random.choice(self.user_agents),
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "Content-Type": "application/json",
            "sec-ch-ua-mobile": "?0",
            "Accept": "*/*",
            "Origin": "https://www.gookaito.com",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://www.gookaito.com/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
    
    def get_random_proxy(self):
        """获取随机代理"""
        if not self.proxy_list:
            return None
        
        proxy_url = random.choice(self.proxy_list)
        if proxy_url.startswith('http://'):
            return {'http': proxy_url, 'https': proxy_url}
        elif proxy_url.startswith('socks5://'):
            return {'http': proxy_url, 'https': proxy_url}
        else:
            return {'http': f'http://{proxy_url}', 'https': f'http://{proxy_url}'}
    
    def send_wallet(self, wallet):
        """发送单个钱包地址"""
        headers = self.get_random_headers()
        data = {"wallet": wallet}
        proxies = self.get_random_proxy()
        
        try:
            response = requests.post(
                self.url,
                headers=headers,
                json=data,
                proxies=proxies,
                timeout=30
            )
            
            if response.status_code == 200:
                self.log_message(f"✅ 钱包 {wallet} 发送成功")
                return True
            else:
                self.log_message(f"❌ 钱包 {wallet} 发送失败，状态码：{response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_message(f"❌ 钱包 {wallet} 发送失败，网络错误：{e}")
            return False
    
    def sending_thread(self):
        """发送线程"""
        try:
            min_delay = float(self.min_delay_var.get())
            max_delay = float(self.max_delay_var.get())
        except ValueError:
            self.log_message("延迟时间格式错误，使用默认值")
            min_delay, max_delay = 1, 5
        
        total = len(self.wallets)
        success_count = 0
        
        self.log_message(f"开始发送 {total} 个钱包地址...")
        self.log_message(f"延迟时间：{min_delay}-{max_delay}秒")
        self.log_message(f"代理数量：{len(self.proxy_list)}")
        self.log_message("-" * 50)
        
        for i, wallet in enumerate(self.wallets):
            if self.stop_sending:
                self.log_message("发送已停止")
                break
            
            self.log_message(f"[{i+1}/{total}] 正在发送钱包：{wallet}")
            
            if self.send_wallet(wallet):
                success_count += 1

            progress = ((i + 1) / total) * 100
            self.progress_var.set(progress)
            
            # 延迟（最后一个不需要延迟）
            if i < total - 1 and not self.stop_sending:
                delay = random.uniform(min_delay, max_delay)
                self.log_message(f"等待 {delay:.2f} 秒...")
                
                sleep_time = 0
                while sleep_time < delay and not self.stop_sending:
                    time.sleep(0.1)
                    sleep_time += 0.1
        
        self.log_message("-" * 50)
        if not self.stop_sending:
            self.log_message(f"发送完成！成功：{success_count}/{total}")
        
        self.is_sending = False
        self.stop_sending = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.load_btn.config(state="normal")
    
    def start_sending(self):
        """开始发送"""
        if not self.wallets:
            messagebox.showerror("错误", "请先加载钱包文件")
            return
        
        result = messagebox.askyesno("确认", f"准备发送 {len(self.wallets)} 个钱包地址，确认开始？")
        if not result:
            return
        
        self.is_sending = True
        self.stop_sending = False
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.load_btn.config(state="disabled")
        self.progress_var.set(0)
        
        thread = threading.Thread(target=self.sending_thread)
        thread.daemon = True
        thread.start()
    
    def stop_sending_func(self):
        """停止发送"""
        if self.is_sending:
            self.stop_sending = True
            self.log_message("正在停止发送...")


def main():
    root = tk.Tk()
    app = WalletSenderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main() 