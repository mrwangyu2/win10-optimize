"""
配置文件解析器
"""
import json
import os
from typing import Dict, List, Optional, Any


class ProfileParser:
    """配置文件解析器类"""
    
    def __init__(self, profile_path: str = "config/win10_optimize_profile.json"):
        """
        初始化解析器
        
        Args:
            profile_path: 配置文件路径
        """
        # 处理 PyInstaller 打包后的路径
        import sys
        if hasattr(sys, '_MEIPASS'):
            # 打包时我们依然把文件放在根目录，或者保持相对路径结构
            # 这里的 profile_path 传入的是 "config/win10_optimize_profile.json"
            self.profile_path = os.path.join(sys._MEIPASS, profile_path)
        else:
            self.profile_path = profile_path

            
        self.profile_data: Optional[Dict[str, Any]] = None

        self.profile_meta: Optional[Dict[str, Any]] = None
        self.categories: Dict[str, Any] = {}
    
    def load_profile(self) -> bool:
        """
        加载配置文件
        
        Returns:
            bool: 是否加载成功
        """
        try:
            if not os.path.exists(self.profile_path):
                raise FileNotFoundError(f"配置文件不存在: {self.profile_path}")
            
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                self.profile_data = json.load(f)
            
            if self.profile_data:
                # 解析元信息
                self.profile_meta = self.profile_data.get('profile', {})
                
                # 解析分类
                self.categories = self.profile_data.get('categories', {})
            
            return True
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return False
    
    def get_profile_info(self) -> Dict[str, Any]:
        """获取配置文件元信息"""
        return self.profile_meta or {}
    
    def get_categories(self) -> List[str]:
        """获取所有分类名称"""
        return list(self.categories.keys())
    
    def get_category_tasks(self, category: str) -> List[Dict[str, Any]]:
        """
        获取指定分类的任务列表
        
        Args:
            category: 分类名称
        
        Returns:
            List[Dict]: 任务列表
        """
        if category not in self.categories:
            return []
        
        return self.categories[category].get('tasks', [])
    
    def get_category_description(self, category: str) -> str:
        """
        获取分类描述
        
        Args:
            category: 分类名称
        
        Returns:
            str: 分类描述
        """
        if category not in self.categories:
            return ""
        
        return self.categories[category].get('description', '')
    
    def validate_profile(self) -> bool:
        """
        验证配置文件有效性
        
        Returns:
            bool: 配置是否有效
        """
        # 检查必要字段
        if not self.profile_meta:
            return False
        
        required_fields = ['name', 'version', 'target_os']
        for field in required_fields:
            if field not in self.profile_meta:
                return False
        
        return True