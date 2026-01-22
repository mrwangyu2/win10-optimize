"""
任务选择器UI
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
from typing import List, Dict, Any
from core.executor import TaskExecutor


class TaskSelector(ttk.Frame):
    """任务选择器组件"""
    
    def __init__(self, parent, parser, initial_selections=None, initial_index=0):
        """
        初始化任务选择器
        
        Args:
            parent: 父组件
            parser: 配置解析器
            initial_selections: 初始选择的任务
            initial_index: 初始显示的分类索引
        """
        super().__init__(parent)
        self.logger = logging.getLogger('TaskSelector')
        self.parser = parser
        self.executor = TaskExecutor()
        
        self.current_category_index = initial_index
        self.categories = parser.get_categories()
        # 使用副本初始化，避免外部修改影响内部状态
        self.selected_tasks: Dict[str, List[Dict[str, Any]]] = initial_selections.copy() if initial_selections else {}
        self.task_vars = []
        self.task_target_vars = []
        self.on_finish = None  # 完成所有分类后的回调钩子
        
        self._create_ui()
        self._load_category()
    
    def _create_ui(self):
        """创建UI组件"""
        # 分类标题
        self.category_label = ttk.Label(
            self,
            text="",
            font=('Arial', 12, 'bold')
        )
        self.category_label.pack(pady=10)
        
        # 描述文本
        self.desc_label = ttk.Label(
            self,
            text="",
            wraplength=650
        )

        self.desc_label.pack(pady=5)
        
        # 主显示区域 (用于显示列表或日志)
        self.display_container = ttk.Frame(self)
        self.display_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 1. 任务列表视图 (Canvas)
        self.list_container = ttk.Frame(self.display_container)
        self.list_container.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.list_container, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.list_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 2. 日志视图 (ScrolledText) - 初始隐藏
        self.log_area = scrolledtext.ScrolledText(
            self.display_container, 
            state='disabled', 
            height=20, 
            font=('Consolas', 9),
            bg="#f8f9fa"
        )
        
        # 按钮框架
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        self.prev_btn = ttk.Button(
            self.button_frame,
            text="上一步",
            command=lambda: self._prev_category()
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.skip_btn = ttk.Button(
            self.button_frame,
            text="跳过",
            command=lambda: self._skip_category()
        )
        self.skip_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = ttk.Button(
            self.button_frame,
            text="下一步",
            command=lambda: self._next_category()
        )
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        self.exec_btn = ttk.Button(
            self.button_frame,
            text="执行优化",
            command=self._execute_optimization,
            style='Accent.TButton'
        )
        # 初始状态不显示
        self.exec_btn.pack_forget()

    def _append_log(self, message: str, level: str = "INFO"):

        """向日志区域添加文本"""
        self.log_area.configure(state='normal')
        tag = level.upper()
        self.log_area.insert(tk.END, f"[{tag}] {message}\n", tag)
        self.log_area.tag_config("ERROR", foreground="red")
        self.log_area.tag_config("SUCCESS", foreground="green")
        self.log_area.tag_config("INFO", foreground="black")
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')
        self.update_idletasks()

    def _load_category(self):
        """加载当前分类"""
        # 按钮状态管理
        self.prev_btn.config(state='normal' if self.current_category_index > 0 else 'disabled')
        self.skip_btn.pack(side=tk.LEFT, padx=5)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        self.exec_btn.pack_forget()
        
        if self.current_category_index >= len(self.categories):
            if hasattr(self, 'on_finish') and self.on_finish:
                # 使用 after 延迟调用，避免在当前组件的方法中销毁自身
                self.after(1, self.on_finish)
            else:
                self._show_summary()
            return

        
        category = self.categories[self.current_category_index]
        # 将标题格式修改为“配置 [分类名称]”
        self.category_label.config(text=f"配置 {category.capitalize()}")
        self.desc_label.config(text=self.parser.get_category_description(category))
        
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        tasks = self.parser.get_category_tasks(category)
        self.task_vars = []
        self.task_target_vars = []
        service_executor = self.executor.executors.get('service')

        header_frame = ttk.Frame(self.scrollable_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(header_frame, text="任务名称", width=45, font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        ttk.Label(header_frame, text="当前状态", width=12, font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        ttk.Label(header_frame, text="目标设置", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)

        for i, task in enumerate(tasks):
            task_id = task.get('id')
            description = task.get('description', task_id)
            status_val, startup_val, status_color = "未知", "未知", "#666666"
            
            if task.get('type') == 'service' and service_executor:
                service_name = task.get('action', {}).get('service_name')
                if service_name:
                    status = service_executor.get_service_status(service_name) # type: ignore
                    status_val, startup_val = status['status'], status['startup']
                    if status_val == "正在运行": status_color = "#28a745"
                    elif status_val == "已停止": status_color = "#6c757d"
                    if startup_val == "禁用": status_color = "#dc3545"
            
            row_frame = ttk.Frame(self.scrollable_frame)
            row_frame.pack(fill=tk.X, padx=10, pady=2)
            
            var = tk.BooleanVar()
            if category in self.selected_tasks:
                var.set(i in [t['index'] for t in self.selected_tasks[category]])
            else:
                var.set(status_val == "正在运行" or startup_val != "禁用")
            self.task_vars.append(var)
            ttk.Checkbutton(row_frame, variable=var).pack(side=tk.LEFT)
            ttk.Label(row_frame, text=description, width=42).pack(side=tk.LEFT, padx=5)
            tk.Label(row_frame, text=f"{status_val} ({startup_val})", fg=status_color, width=12, anchor="w").pack(side=tk.LEFT, padx=5)


            target_var = tk.StringVar(value="disabled")
            if category in self.selected_tasks:
                for t in self.selected_tasks[category]:
                    if t['index'] == i: target_var.set(t.get('target', 'disabled')); break
            self.task_target_vars.append(target_var)
            
            for val in ["禁用", "手动", "自动"]:
                v = {"禁用": "disabled", "手动": "manual", "自动": "automatic"}[val]
                ttk.Radiobutton(row_frame, text=val, variable=target_var, value=v).pack(side=tk.LEFT, padx=2)

    def _save_selection(self):
        """保存当前选择"""
        if self.current_category_index < len(self.categories):
            category = self.categories[self.current_category_index]
            selected = []
            for i, var in enumerate(self.task_vars):
                if var.get():
                    selected.append({'index': i, 'target': self.task_target_vars[i].get()})
            self.selected_tasks[category] = selected
    
    def _prev_category(self):
        self._save_selection(); self.current_category_index -= 1; self._load_category()
    
    def _next_category(self):
        self._save_selection(); self.current_category_index += 1; self._load_category()
    
    def _skip_category(self):
        """跳过当前分类：不保存当前界面选择，直接进入下一步"""
        if self.current_category_index < len(self.categories):
            category = self.categories[self.current_category_index]
            self.selected_tasks[category] = []  # 显式清空该分类的选择
            self.current_category_index += 1
            self._load_category()

    
    def _show_summary(self):
        """显示总结"""
        # 按钮状态管理
        self.skip_btn.pack_forget()
        self.next_btn.pack_forget()
        
        total_tasks = sum(len(tasks) for tasks in self.selected_tasks.values())
        self.category_label.config(text="优化总结")
        
        # 仅在有任务时显示执行按钮
        if total_tasks > 0:
            self.desc_label.config(text=f"您已选择 {total_tasks} 个优化任务\n点击'执行优化'开始")
            self.exec_btn.pack(side=tk.RIGHT, padx=5)
        else:
            self.exec_btn.pack_forget()
            self.desc_label.config(text="未选择任何优化任务，请返回上一步选择。")
        
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()


        target_map = {"disabled": "禁用", "manual": "手动", "automatic": "自动"}
        for category, items in self.selected_tasks.items():
            if items:
                ttk.Label(self.scrollable_frame, text=f"[{category}]", font=('Arial', 10, 'bold')).pack(fill=tk.X, padx=10, pady=(10, 2))
                
                # 如果是特殊的更新策略项或网络配置项（已经在应用时格式化好了）
                if category in ["更新策略", "网络配置"]:

                    for item in items:
                        ttk.Label(self.scrollable_frame, text=f"  - {item.get('description', '')}").pack(fill=tk.X, padx=20, pady=1)
                    continue


                tasks = self.parser.get_category_tasks(category)
                for item in items:
                    idx, target = item['index'], item['target']
                    desc = tasks[idx].get('description', '')
                    ttk.Label(self.scrollable_frame, text=f"  - {desc} -> 设为: {target_map.get(target, target)}").pack(fill=tk.X, padx=20, pady=1)

    def _execute_optimization(self):
        """执行优化并显示详细日志"""
        all_tasks = []
        
        # 调试日志：输出当前已选择的任务分类
        self.logger.info(f"开始构建任务列表。当前已选择分类: {list(self.selected_tasks.keys())}")
        
        # 预处理：将更新策略和网络配置以外的任务加入列表
        for category, items in self.selected_tasks.items():
            if category in ["更新策略", "网络配置"]:
                continue 

            
            tasks = self.parser.get_category_tasks(category)
            if not tasks:
                self.logger.warning(f"分类 {category} 未找到任何任务定义")
                continue
                
            for item in items:
                idx, target = item['index'], item['target']
                if idx < len(tasks):
                    task_copy = tasks[idx].copy()
                    if 'action' in task_copy:
                        task_copy['action'] = task_copy['action'].copy()
                        task_copy['action']['startup_type'] = target
                    all_tasks.append(task_copy)
                else:
                    self.logger.error(f"索引越界: 分类 {category}, 索引 {idx}, 任务总数 {len(tasks)}")
        
        # 检查是否选择了任何优化任务
        update_items = self.selected_tasks.get("更新策略", [])
        network_items = self.selected_tasks.get("网络配置", [])
        if not all_tasks and not update_items and not network_items:
            messagebox.showinfo("提示", "未选择任何优化任务")
            return
            
        confirm_msg = f"即将执行 {len(all_tasks) + len(update_items) + len(network_items)} 个优化任务\n是否继续?"

        if not messagebox.askyesno("确认", confirm_msg):
            return
        
        # 切换到日志视图
        self.list_container.pack_forget()
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.category_label.config(text="正在执行优化...")
        self.desc_label.config(text="请查看下方实时日志输出")
        
        # 禁用导航按钮
        self.prev_btn.config(state='disabled')
        self.skip_btn.config(state='disabled')
        self.next_btn.config(state='disabled')
        self.exec_btn.config(state='disabled')

        # 执行任务并记录日志
        success_count = 0
        failed_count = 0
        
        # 获取特殊任务项
        update_items = self.selected_tasks.get("更新策略", [])
        network_items = self.selected_tasks.get("网络配置", [])
        total_count = len(all_tasks) + len(update_items) + len(network_items)
        
        self._append_log(f"开始执行优化流程，共 {total_count} 个任务...", "INFO")
        
        # 1. 显示已应用的特殊策略状态
        for item in update_items + network_items:
            self._append_log(f"成功: {item.get('description', '')} (已应用)", "SUCCESS")
            success_count += 1



        # 2. 执行其他任务
        for task in all_tasks:
            task_id = task.get('id', 'unknown')
            desc = task.get('description', task_id)
            target = task.get('action', {}).get('startup_type', 'disabled')
            target_map = {"disabled": "禁用", "manual": "手动", "automatic": "自动"}
            
            self._append_log(f"正在处理: {desc} (目标: {target_map.get(target, target)})")
            
            task_type = str(task.get('type', ''))
            executor = self.executor.executors.get(task_type)
            
            if not executor:
                self._append_log(f"错误: 未找到类型为 {task_type} 的执行器", "ERROR")
                failed_count += 1
                continue
                
            try:
                if executor.execute(task):
                    self._append_log(f"成功: {desc} 已配置完成", "SUCCESS")
                    success_count += 1
                else:
                    # 尝试从 logger 中获取最后一条错误信息，或者此处由执行器抛出异常处理
                    self._append_log(f"失败: {desc} 执行器返回失败。请检查是否被安全软件拦截或权限不足。", "ERROR")
                    failed_count += 1
            except Exception as e:
                # 捕获具体的异常并显示在 UI 日志中
                err_msg = str(e)
                if "拒绝访问" in err_msg or "Access is denied" in err_msg:
                    err_msg = "拒绝访问（请检查管理员权限或杀毒软件拦截）"
                self._append_log(f"异常: {desc} - {err_msg}", "ERROR")
                failed_count += 1


        self._append_log("-" * 40)
        self._append_log(f"优化完成！成功: {success_count}, 失败: {failed_count}", "INFO")
        
        self.category_label.config(text="优化执行完毕")
        messagebox.showinfo("完成", f"优化任务已执行完毕\n成功: {success_count}\n失败: {failed_count}", parent=self.winfo_toplevel())
        
        # 清理已执行的任务列表
        self.selected_tasks.clear()
        
        # 允许点击“上一步”返回查看状态，但不允许再次“执行”以防重复操作



        self.prev_btn.config(state='normal')
        self.exec_btn.config(text="执行完毕", state='disabled')
