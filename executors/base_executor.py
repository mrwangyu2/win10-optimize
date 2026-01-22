"""
执行器基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging


class BaseExecutor(ABC):
    """执行器基类"""
    
    def __init__(self):
        """初始化执行器"""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> bool:
        """
        执行任务
        
        Args:
            task: 任务配置
        
        Returns:
            bool: 执行是否成功
        """
        pass
    
    @abstractmethod
    def rollback(self, task: Dict[str, Any]) -> bool:
        """
        回滚任务
        
        Args:
            task: 任务配置
        
        Returns:
            bool: 回滚是否成功
        """
        pass
    
    def validate_task(self, task: Dict[str, Any]) -> bool:
        """
        验证任务配置
        
        Args:
            task: 任务配置
        
        Returns:
            bool: 配置是否有效
        """
        required_fields = ['id', 'type', 'action']
        return all(field in task for field in required_fields)