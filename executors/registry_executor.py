"""
注册表执行器
"""
import winreg
from typing import Dict, Any
from executors.base_executor import BaseExecutor
from utils.admin_check import require_admin


class RegistryExecutor(BaseExecutor):
    """注册表执行器"""
    
    # 注册表根键映射
    ROOT_KEYS = {
        'HKLM': winreg.HKEY_LOCAL_MACHINE,
        'HKCU': winreg.HKEY_CURRENT_USER,
        'HKCR': winreg.HKEY_CLASSES_ROOT,
        'HKU': winreg.HKEY_USERS,
        'HKCC': winreg.HKEY_CURRENT_CONFIG
    }
    
    # 注册表类型映射
    REG_TYPES = {
        'REG_DWORD': winreg.REG_DWORD,
        'REG_SZ': winreg.REG_SZ,
        'REG_BINARY': winreg.REG_BINARY,
        'REG_EXPAND_SZ': winreg.REG_EXPAND_SZ
    }
    
    @require_admin
    def execute(self, task: Dict[str, Any]) -> bool:
        """
        执行注册表修改任务
        
        Args:
            task: 任务配置
        
        Returns:
            bool: 执行是否成功
        """
        try:
            action = task.get('action', {})
            root = action.get('root')
            path = action.get('path')
            values = action.get('values', [])
            
            if not all([root, path, values]):
                self.logger.error("注册表配置不完整")
                return False
            
            root_key = self.ROOT_KEYS.get(str(root))
            if root_key is None:
                self.logger.error(f"无效的注册表根键: {root}")
                return False
            
            # 打开或创建注册表键
            key = winreg.CreateKey(root_key, str(path))

            
            # 设置值
            for value_info in values:
                name = value_info.get('name')
                value = value_info.get('value')
                reg_type = self.REG_TYPES.get(
                    value_info.get('type', 'REG_DWORD'),
                    winreg.REG_DWORD
                )
                
                winreg.SetValueEx(key, name, 0, reg_type, value)
                self.logger.info(f"设置注册表值: {path}\\{name}")
            
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            self.logger.error(f"执行注册表任务失败: {e}")
            return False
    
    @require_admin
    def rollback(self, task: Dict[str, Any]) -> bool:
        """
        回滚注册表修改
        
        Args:
            task: 任务配置
        
        Returns:
            bool: 回滚是否成功
        """
        try:
            action = task.get('action', {})
            rollback = task.get('rollback', {})
            root = action.get('root')
            path = action.get('path')
            delete_values = rollback.get('delete_values', [])
            
            if not all([root, path]):
                return False
            
            root_key = self.ROOT_KEYS.get(str(root))
            if root_key is None:
                return False
            
            key = winreg.OpenKey(root_key, str(path), 0, winreg.KEY_WRITE)

            
            # 删除指定的值
            for value_name in delete_values:
                try:
                    winreg.DeleteValue(key, value_name)
                    self.logger.info(f"删除注册表值: {path}\\{value_name}")
                except FileNotFoundError:
                    pass
            
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            self.logger.error(f"回滚注册表任务失败: {e}")
            return False