"""
Win10优化工具 - 主程序入口
"""
import sys
from ui.main_window import MainWindow
from utils.admin_check import check_admin_privileges
from utils.logger import setup_logger


def main():
    """主函数"""
    logger = setup_logger()
    
    # 检查管理员权限
    if not check_admin_privileges():
        logger.warning("程序未以管理员权限运行")
        if sys.platform == 'win32':
            import ctypes
            # 弹出标准 Windows 对话框确认是否提升权限
            from tkinter import messagebox
            response = messagebox.askyesno("权限请求", "程序检测到当前未以管理员权限运行，大部分优化功能将无法生效。\n\n是否尝试以管理员身份重新启动？")
            
            if response:
                try:
                    # 尝试重新以管理员权限启动
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                    sys.exit(0)
                except Exception as e:
                    logger.error(f"无法请求管理员权限: {e}")
                    messagebox.showerror("提权失败", f"无法请求管理员权限: {e}\n请手动右键点击程序并选择“以管理员身份运行”。")
            else:
                messagebox.showwarning("权限限制", "您选择了继续运行，但请注意，如果没有管理员权限，优化任务极有可能执行失败。")


    
    # 启动GUI
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        logger.error(f"程序运行错误: {e}")
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()