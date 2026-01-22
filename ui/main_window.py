"""
主窗口UI
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from core.profile_parser import ProfileParser
from core.system_checker import SystemChecker
from ui.task_selector import TaskSelector
from ui.update_pause_selector import UpdatePauseSelector
from ui.bandwidth_selector import NetworkConfigSelector


class MainWindow:

    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        self.logger = logging.getLogger('MainWindow')
        self.root = tk.Tk()
        self.root.title("Win10 优化工具")
        
        # 设置窗口大小并居中
        window_width = 700
        window_height = 580
        
        # 强制刷新以获取正确的屏幕尺寸
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        # 初始化解析器

        self.parser = ProfileParser()
        self.task_selector = None
        self.selected_tasks_cache = {}  # 用于在界面切换时保持状态
        
        # 创建UI
        self._create_ui()
        
        # 加载配置
        self._load_profile()
    
    def _create_ui(self):
        """创建UI组件"""
        # 顶部信息栏
        info_frame = ttk.Frame(self.root, padding="10")
        info_frame.pack(fill=tk.X)
        
        self.info_label = ttk.Label(
            info_frame,
            text="Win10 优化工具",
            font=('Arial', 14, 'bold')
        )
        self.info_label.pack()
        
        # 主内容区
        self.content_frame = ttk.Frame(self.root, padding="10")
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 底部按钮栏
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 开发者信息
        dev_info = tk.Label(
            button_frame, 
            text="开发者: 王宇 | 邮箱: wangyuxxx@163.com",
            font=('Arial', 8),
            fg="#888888"
        )
        dev_info.pack(side=tk.LEFT)
        
        ttk.Button(
            button_frame,
            text="退出",
            command=self.root.quit
        ).pack(side=tk.RIGHT, padx=5)

    
    def _load_profile(self):
        """加载配置文件"""
        if not self.parser.load_profile():
            messagebox.showerror("错误", "无法加载配置文件")
            return
        
        # 验证配置
        if not self.parser.validate_profile():
            messagebox.showerror("错误", "配置文件格式无效")
            return
        
        # 检查系统兼容性
        profile_info = self.parser.get_profile_info()
        target_os = profile_info.get('target_os', '')
        
        if not SystemChecker.check_os_compatibility(target_os):
            messagebox.showwarning(
                "警告",
                f"当前系统可能不兼容此配置\n目标系统: {target_os}"
            )
        
        # 更新信息栏
        self.info_label.config(
            text=f"{profile_info.get('name', '')} v{profile_info.get('version', '')}"
        )
        
        # 默认显示任务选择器（第一步）
        self._show_task_selector()
    
    def _clear_content(self):
        """清空内容区"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_task_selector(self, index=0):
        """显示任务选择器（第一步：禁止服务）"""
        self._clear_content()
        # 创建或恢复 task_selector
        self.task_selector = TaskSelector(
            self.content_frame, 
            self.parser, 
            initial_selections=self.selected_tasks_cache,
            initial_index=index
        )
        self.task_selector.pack(fill=tk.BOTH, expand=True)
        # 注入下一步的路由逻辑：当所有分类完成时，跳转到更新暂停界面
        self.task_selector.on_finish = self._show_update_pause_selector

    def _show_update_pause_selector(self):
        """显示更新暂停设置界面（第二步：单独界面）"""
        # 保存第一步的选择到缓存
        if self.task_selector:
            self.task_selector._save_selection()
            # 显式复制选择内容，防止引用丢失或被后续实例误删
            self.selected_tasks_cache.update(self.task_selector.selected_tasks.copy())
            
        self._clear_content()
        update_selector = UpdatePauseSelector(
            self.content_frame, 
            self.parser,
            on_back=lambda: self._show_task_selector(len(self.parser.get_categories()) - 1),
            on_next=self._show_bandwidth_selector,
            on_apply=self._save_update_policy
        )
        update_selector.pack(fill=tk.BOTH, expand=True)

    def _show_bandwidth_selector(self):
        """显示网络配置设置界面（第三步：单独界面）"""
        self._clear_content()
        bandwidth_selector = NetworkConfigSelector(
            self.content_frame,
            self.parser,
            on_back=self._show_update_pause_selector,
            on_next=self._show_summary_from_update,
            on_apply=self._save_bandwidth_policy
        )
        bandwidth_selector.pack(fill=tk.BOTH, expand=True)


    def _save_update_policy(self, days):
        """保存更新策略任务到缓存"""
        update_task = {
            'index': 0,
            'target': f"{days} 天",
            'is_registry': True,
            'description': f"Windows 更新最大暂停天数 -> {days}"
        }
        # 使用 update 确保不覆盖已有的服务选择
        self.selected_tasks_cache["更新策略"] = [update_task]

    def _save_bandwidth_policy(self, limit, tcp_level=None):
        """保存网络配置任务到缓存"""
        tasks = []
        
        # 1. 带宽限制任务
        tasks.append({
            'index': 0,
            'target': f"{limit}%",
            'is_registry': True,
            'description': f"系统保留带宽限制 -> {limit}%"
        })
        
        # 2. TCP 吞吐量任务
        if tcp_level is not None:
            level_name = {"0": "关闭 (disabled)", "1": "常规 (normal)", "2": "实验性 (experimental)"}.get(tcp_level, tcp_level)
            tasks.append({
                'index': 1,
                'target': level_name,
                'is_registry': True,
                'description': f"入站 TCP 吞吐量级别 -> {level_name}"
            })
            
        self.selected_tasks_cache["网络配置"] = tasks



    def _show_summary_from_update(self):
        """从带宽设置界面进入总结界面（第四步：总结）"""
        self._clear_content()
        # 重新创建 TaskSelector 并载入之前的选择，直接跳转到总结状态
        categories = self.parser.get_categories()
        self.task_selector = TaskSelector(
            self.content_frame, 
            self.parser, 
            initial_selections=self.selected_tasks_cache,
            initial_index=len(categories)
        )
        self.task_selector.pack(fill=tk.BOTH, expand=True)
        
        # 注入清理回调：当执行完成后，清理主窗口的缓存
        original_execute = self.task_selector._execute_optimization
        def wrapped_execute():
            original_execute()
            self.selected_tasks_cache.clear()
        
        self.task_selector._execute_optimization = wrapped_execute
        
        # 特殊处理：修改总结界面的“上一步”按钮，使其返回到带宽设置界面
        self.task_selector.prev_btn.config(command=self._show_bandwidth_selector)


    def run(self):
        """运行主窗口"""
        self.root.mainloop()
