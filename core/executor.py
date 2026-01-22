"""
任务执行器核心
"""
import logging
from typing import List, Dict, Any
from executors.service_executor import ServiceExecutor
from executors.registry_executor import RegistryExecutor


class TaskExecutor:
    """任务执行管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger('TaskExecutor')
        self.executors = {
            'service': ServiceExecutor(),
            'registry': RegistryExecutor()
        }
    
    def execute_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        执行一系列任务
        
        Args:
            tasks: 任务列表
            
        Returns:
            Dict[str, int]: 执行统计信息 (success, failed)
        """
        stats = {'success': 0, 'failed': 0}
        
        for task in tasks:
            task_id = task.get('id', 'unknown')
            task_type = str(task.get('type', ''))
            
            self.logger.info(f"正在执行任务: {task_id} ({task_type})")
            
            executor = self.executors.get(task_type)

            if not executor:
                self.logger.error(f"未找到类型为 {task_type} 的执行器")
                stats['failed'] += 1
                continue
            
            try:
                success = executor.execute(task)
                if success:
                    stats['success'] += 1
                else:
                    stats['failed'] += 1
            except Exception as e:
                self.logger.error(f"任务 {task_id} 执行出错: {e}")
                stats['failed'] += 1
        
        return stats

    def rollback_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        回滚一系列任务
        
        Args:
            tasks: 任务列表
            
        Returns:
            Dict[str, int]: 执行统计信息 (success, failed)
        """
        stats = {'success': 0, 'failed': 0}
        
        for task in tasks:
            task_id = task.get('id', 'unknown')
            task_type = str(task.get('type', ''))
            
            self.logger.info(f"正在回滚任务: {task_id} ({task_type})")
            
            executor = self.executors.get(task_type)

            if not executor:
                self.logger.error(f"未找到类型为 {task_type} 的执行器")
                stats['failed'] += 1
                continue
            
            try:
                success = executor.rollback(task)
                if success:
                    stats['success'] += 1
                else:
                    stats['failed'] += 1
            except Exception as e:
                self.logger.error(f"任务 {task_id} 回滚出错: {e}")
                stats['failed'] += 1
        
        return stats
