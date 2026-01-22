"""
管理员权限检查模块
"""
import ctypes


def check_admin_privileges() -> bool:

    """
    检查是否具有管理员权限
    
    Returns:
        bool: True表示有管理员权限
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def require_admin(func):
    """
    装饰器：要求管理员权限
    
    Args:
        func: 被装饰的函数
    
    Returns:
        wrapper: 包装函数
    """
    def wrapper(*args, **kwargs):
        if not check_admin_privileges():
            raise PermissionError("此操作需要管理员权限")
        return func(*args, **kwargs)
    return wrapper