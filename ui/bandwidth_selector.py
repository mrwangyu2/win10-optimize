"""
网络带宽限制设置界面
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import winreg
import subprocess
import os


class NetworkConfigSelector(ttk.Frame):
    """专门用于网络配置优化（如系统保留带宽限制、TCP 吞吐量）的界面"""
    
    REG_PATH = r"SOFTWARE\Policies\Microsoft\Windows\Psched"
    REG_VALUE_NAME = "NonBestEffortLimit"

    def __init__(self, parent, parser, on_back=None, on_next=None, on_apply=None):
        super().__init__(parent)
        self.logger = logging.getLogger('NetworkConfigSelector')
        self.parser = parser
        self.on_back = on_back
        self.on_next = on_next
        self.on_apply = on_apply
        
        self.total_ram_gb = self._get_total_ram()
        self._create_ui()
        self._load_current_values()

    def _get_total_ram(self):
        """获取系统总内存 (GB)"""
        try:
            # 使用 wmic 获取内存字节数
            output = subprocess.check_output('wmic computersystem get totalphysicalmemory', shell=True).decode()
            memory_bytes = int(output.split('\n')[1].strip())
            return memory_bytes / (1024**3)
        except Exception:
            return 8.0  # 默认假设 8G

    def _create_ui(self):
        """创建专门的设置界面"""
        # 标题
        ttk.Label(
            self,
            text="网络配置优化",
            font=('Arial', 12, 'bold')
        ).pack(pady=10)

        # 1. 带宽限制设置
        bw_frame = ttk.LabelFrame(self, text="系统保留带宽 (QoS)", padding=15)
        bw_frame.pack(pady=5, padx=20, fill=tk.X)

        ttk.Label(
            bw_frame,
            text="Windows 默认会为重要流量保留一部分带宽。设置为 0% 可解除限制。",
            wraplength=650,
            justify=tk.LEFT
        ).pack(pady=5, anchor=tk.W)


        self.bw_current_label = tk.Label(
            bw_frame, 
            text="当前设置: 正在查询...",
            fg="#0066cc",
            font=('Arial', 9, 'bold')
        )
        self.bw_current_label.pack(pady=2, anchor=tk.W)


        bw_input_frame = ttk.Frame(bw_frame)
        bw_input_frame.pack(pady=5, fill=tk.X)
        ttk.Label(bw_input_frame, text="保留百分比 (0-100):").pack(side=tk.LEFT)
        self.limit_var = tk.StringVar(value="0")
        ttk.Entry(bw_input_frame, textvariable=self.limit_var, width=10).pack(side=tk.LEFT, padx=10)
        ttk.Label(bw_input_frame, text="%").pack(side=tk.LEFT)
        ttk.Button(bw_input_frame, text="推荐值 (0%)", command=lambda: self.limit_var.set("0")).pack(side=tk.LEFT, padx=5)

        # 2. TCP 吞吐量设置
        tcp_frame = ttk.LabelFrame(self, text="入站 TCP 吞吐量级别", padding=15)
        tcp_frame.pack(pady=5, padx=20, fill=tk.X)

        ttk.Label(
            tcp_frame,
            text="根据内存大小优化 TCP 接收窗口自动调优级别，提升网络吞吐量。",
            wraplength=650,
            justify=tk.LEFT
        ).pack(pady=5, anchor=tk.W)


        self.tcp_current_label = tk.Label(
            tcp_frame, 
            text="当前设置: 正在查询...",
            fg="#0066cc",
            font=('Arial', 9, 'bold')
        )
        self.tcp_current_label.pack(pady=2, anchor=tk.W)


        # 推荐逻辑
        rec_level = "1"
        if self.total_ram_gb >= 15.5: # 16G
            rec_level = "2"
        elif self.total_ram_gb >= 3.5: # 4G
            rec_level = "1"
        
        self.tcp_level_var = tk.StringVar(value=rec_level)
        
        tcp_input_frame = ttk.Frame(tcp_frame)
        tcp_input_frame.pack(pady=5, fill=tk.X)
        
        ttk.Label(tcp_input_frame, text="吞吐量级别:").pack(side=tk.LEFT)
        
        # 级别选择
        levels = [("级别 0 (关闭)", "0"), ("级别 1 (常规)", "1"), ("级别 2 (实验性)", "2")]
        for text, val in levels:
            rb = ttk.Radiobutton(tcp_input_frame, text=text, variable=self.tcp_level_var, value=val)
            rb.pack(side=tk.LEFT, padx=10)
            
        self.ram_info_label = ttk.Label(tcp_frame, text=f"系统检测到内存: {self.total_ram_gb:.1f} GB，已为您选择推荐项。", foreground="blue")
        self.ram_info_label.pack(pady=5, anchor=tk.W)

        # 底部按钮
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=20)

        ttk.Button(
            nav_frame,
            text="上一步",
            command=self._go_back
        ).pack(side=tk.LEFT, padx=5)

        self.skip_btn = ttk.Button(
            nav_frame,
            text="跳过",
            command=self._go_next
        )
        self.skip_btn.pack(side=tk.LEFT, padx=5)

        self.apply_btn = ttk.Button(
            nav_frame,
            text="下一步",
            command=self._apply_settings,
            style='Accent.TButton'
        )
        self.apply_btn.pack(side=tk.LEFT, padx=5)

        # 监听输入变化
        self.limit_var.trace_add("write", lambda *args: self.apply_btn.config(state='normal'))
        self.tcp_level_var.trace_add("write", lambda *args: self.apply_btn.config(state='normal'))

    def _load_current_values(self):
        """加载当前设置值"""
        # 加载带宽
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self.REG_PATH, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, self.REG_VALUE_NAME)
                self.bw_current_label.config(text=f"当前设置: {value}%")
        except FileNotFoundError:
            self.bw_current_label.config(text="当前设置: 默认 (20%)")
        except Exception:
            self.bw_current_label.config(text="当前设置: 查询失败")

        # 加载 TCP 级别 (通过 netsh 判定)
        try:
            output = subprocess.check_output('netsh int tcp show global', shell=True).decode('gbk')
            if "normal" in output or "常规" in output:
                self.tcp_current_label.config(text="当前设置: 级别 1 (normal)")
            elif "experimental" in output or "实验性" in output:
                self.tcp_current_label.config(text="当前设置: 级别 2 (experimental)")
            elif "disabled" in output or "禁用" in output:
                self.tcp_current_label.config(text="当前设置: 级别 0 (disabled)")
            else:
                self.tcp_current_label.config(text="当前设置: 其他/未知")
        except Exception:
            self.tcp_current_label.config(text="当前设置: 查询失败")

    def _apply_settings(self):
        """应用所有网络设置"""
        try:
            # 1. 应用带宽
            bw_val = int(self.limit_var.get())
            if not (0 <= bw_val <= 100): raise ValueError
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, self.REG_PATH) as key:
                winreg.SetValueEx(key, self.REG_VALUE_NAME, 0, winreg.REG_DWORD, bw_val)

            # 2. 应用 TCP 级别
            tcp_level = self.tcp_level_var.get()
            tcp_cmd_val = {"0": "disabled", "1": "normal", "2": "experimental"}[tcp_level]
            subprocess.check_call(f'netsh int tcp set global autotuninglevel={tcp_cmd_val}', shell=True)

            # 3. 回调通知主窗口保存
            if self.on_apply:
                # 传递一个字典或特定格式，让主窗口能同时保存两项
                self.on_apply(bw_val, tcp_level)

            self._go_next()

        except Exception as e:
            messagebox.showerror("错误", f"应用设置失败: {str(e)}")

    def _go_back(self):

        """返回上一步"""
        if self.on_back:
            self.on_back()

    def _go_next(self):
        """进入下一步（总结）"""
        if self.on_next:
            self.on_next()
