"""
服务执行器
"""
import subprocess
from typing import Dict, Any
from executors.base_executor import BaseExecutor
from utils.admin_check import require_admin


class ServiceExecutor(BaseExecutor):
    """Windows服务执行器"""
    
    @require_admin
    def execute(self, task: Dict[str, Any]) -> bool:
        """
        执行服务配置任务
        
        Args:
            task: 任务配置
        
        Returns:
            bool: 执行是否成功
        """
        try:
            action = task.get('action', {})
            service_name = action.get('service_name')
            startup_type = action.get('startup_type')
            stop_service = action.get('stop_service', False)
            
            if not service_name:
                self.logger.error("服务名称未指定")
                return False
            
            # 停止服务
            if stop_service:
                self._stop_service(service_name)
            
            # 设置启动类型
            if startup_type:
                self._set_startup_type(service_name, startup_type)
            
            self.logger.info(f"服务 {service_name} 配置成功")
            return True
            
        except Exception as e:
            self.logger.error(f"执行服务任务失败: {e}")
            return False
    
    @require_admin
    def rollback(self, task: Dict[str, Any]) -> bool:
        """
        回滚服务配置
        
        Args:
            task: 任务配置
        
        Returns:
            bool: 回滚是否成功
        """
        try:
            action = task.get('action', {})
            rollback = task.get('rollback', {})
            service_name = action.get('service_name')
            startup_type = rollback.get('startup_type')
            
            if service_name and startup_type:
                self._set_startup_type(service_name, startup_type)
                self.logger.info(f"服务 {service_name} 回滚成功")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"回滚服务任务失败: {e}")
            return False
    
    def _stop_service(self, service_name: str):
        """停止服务"""
        cmd = f'sc stop "{service_name}"'
        subprocess.run(cmd, shell=True, capture_output=True)
    
    def _set_startup_type(self, service_name: str, startup_type: str):
        """设置服务启动类型"""
        # 映射 UI 友好名称到 sc 命令参数
        mapping = {
            'manual': 'demand',
            'automatic': 'auto',
            'disabled': 'disabled',
            'demand': 'demand',
            'auto': 'auto'
        }
        real_type = mapping.get(startup_type.lower(), startup_type)
        
        cmd = f'sc config "{service_name}" start= {real_type}'
        result = subprocess.run(cmd, shell=True, capture_output=True)
        
        if result.returncode != 0:
            error_msg = result.stderr.decode('gbk', errors='ignore').strip()
            raise Exception(f"SC 错误: {error_msg}")


    def get_service_status(self, service_name: str) -> Dict[str, str]:
        """
        获取服务当前状态
        
        Returns:
            Dict: {'status': 'RUNNING'|'STOPPED'|'UNKNOWN', 'startup': 'auto'|'manual'|'disabled'|'unknown'}
        """
        status_info = {'status': 'UNKNOWN', 'startup': 'unknown'}
        try:
            # 获取状态
            query_cmd = f'sc query "{service_name}"'
            result = subprocess.run(query_cmd, shell=True, capture_output=True, text=True)
            if "STATE" in result.stdout:
                if "RUNNING" in result.stdout:
                    status_info['status'] = '正在运行'
                elif "STOPPED" in result.stdout:
                    status_info['status'] = '已停止'

            # 获取启动类型
            config_cmd = f'sc qc "{service_name}"'
            result = subprocess.run(config_cmd, shell=True, capture_output=True, text=True)
            if "START_TYPE" in result.stdout:
                if "AUTO_START" in result.stdout:
                    status_info['startup'] = '自动'
                elif "DEMAND_START" in result.stdout:
                    status_info['startup'] = '手动'
                elif "DISABLED" in result.stdout:
                    status_info['startup'] = '禁用'
        except Exception:
            pass
        return status_info
