"""
系统检查模块
"""
import platform


class SystemChecker:
    """系统检查器类"""
    
    @staticmethod
    def check_os_compatibility(target_os: str) -> bool:
        """
        检查操作系统兼容性
        
        Args:
            target_os: 目标操作系统
        
        Returns:
            bool: 是否兼容
        """
        current_os = platform.system()
        
        if current_os != "Windows":
            return False
        
        version = platform.version()
        
        if "Windows-10" in target_os or "Windows 10" in target_os:
            return "10" in version
        
        return True
    
    @staticmethod
    def get_system_info() -> dict[str, str]:
        """
        获取系统信息
        
        Returns:
            dict: 系统信息字典
        """
        return {

            'system': platform.system(),
            'version': platform.version(),
            'release': platform.release(),
            'machine': platform.machine()
        }