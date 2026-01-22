"""
Windows 更新暂停设置界面
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import winreg
from typing import Optional


class UpdatePauseSelector(ttk.Frame):
    """专门用于设置 Windows 更新暂停天数的界面"""
    
    REG_PATH = r"SOFTWARE\Microsoft\WindowsUpdate\UX\Settings"
    REG_VALUE_NAME = "FlightSettingsMaxPauseDays"

    def __init__(self, parent, parser, on_back=None, on_next=None, on_apply=None):
        super().__init__(parent)
        self.logger = logging.getLogger('UpdatePauseSelector')
        self.parser = parser
        self.on_back = on_back
        self.on_next = on_next
        self.on_apply = on_apply
        
        self._create_ui()
        self._load_current_value()

    def _create_ui(self):
        """创建专门的设置界面"""
        # 标题
        ttk.Label(
            self,
            text="Windows 更新暂停策略",
            font=('Arial', 12, 'bold')
        ).pack(pady=10)

        # 描述
        desc_text = "此设置可以修改 Windows 更新界面允许暂停的最大天数上限。\n修改后，您可以在系统的“更新和安全 -> 暂停更新”中看到更多可选天数。"
        ttk.Label(
            self,
            text=desc_text,
            wraplength=650,
            justify=tk.LEFT
        ).pack(pady=10, padx=20)

        # 输入区域框架
        input_frame = ttk.LabelFrame(self, text="设置选项", padding=20)
        input_frame.pack(pady=10, padx=20, fill=tk.X)


        # 当前值显示
        self.current_val_label = tk.Label(
            input_frame, 
            text="当前系统设置: 正在查询...",
            fg="#0066cc",
            font=('Arial', 9, 'bold')
        )
        self.current_val_label.pack(pady=5, anchor=tk.W)


        # 输入框
        entry_frame = ttk.Frame(input_frame)
        entry_frame.pack(pady=10, fill=tk.X)
        
        ttk.Label(entry_frame, text="最大暂停天数 (建议 36542):").pack(side=tk.LEFT)
        
        self.days_var = tk.StringVar(value="36542")
        self.days_entry = ttk.Entry(entry_frame, textvariable=self.days_var, width=15)
        self.days_entry.pack(side=tk.LEFT, padx=10)

        # 快速设置按钮
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(pady=10, fill=tk.X)
        
        ttk.Button(btn_frame, text="推荐值 (36542天)", command=lambda: self.days_var.set("36542")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="恢复默认 (35天)", command=lambda: self.days_var.set("35")).pack(side=tk.LEFT, padx=5)

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
            command=self._apply_setting,
            style='Accent.TButton'
        )
        self.apply_btn.pack(side=tk.LEFT, padx=5)
        self.apply_btn.config(state='disabled') # 默认禁用


        # 监听输入变化
        self.days_var.trace_add("write", lambda *args: self._on_input_change())

    def _on_input_change(self):
        """当输入改变时启用下一步按钮"""
        self.apply_btn.config(state='normal')

    def _load_current_value(self):
        """从注册表读取当前值"""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self.REG_PATH, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, self.REG_VALUE_NAME)
                self.current_val_label.config(text=f"当前系统设置: {value} 天")
        except FileNotFoundError:
            self.current_val_label.config(text="当前系统设置: 默认 (未设置)")
        except Exception as e:
            self.current_val_label.config(text=f"当前系统设置: 查询失败 ({str(e)})")

    def _apply_setting(self):
        """执行注册表修改"""
        try:
            days_str = self.days_var.get()
            days = int(days_str)
            if days < 0: raise ValueError
            
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, self.REG_PATH) as key:
                winreg.SetValueEx(key, self.REG_VALUE_NAME, 0, winreg.REG_DWORD, days)
            
            # 使用回调通知主窗口保存此任务
            if self.on_apply:
                self.on_apply(days)

            self._load_current_value()
            # 应用成功后直接进入下一步
            self._go_next()

        except ValueError:
            messagebox.showerror("错误", "请输入有效的正整数。")
        except PermissionError:
            messagebox.showerror("错误", "权限不足。请以管理员身份运行此程序。")
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
