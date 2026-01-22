"""
日志管理模块
"""
import logging
import os
from datetime import datetime


def setup_logger(log_dir: str = "logs"):

    """
    设置日志记录器
    
    Args:
        log_dir: 日志目录
    
    Returns:
        logger: 日志记录器实例
    """
    # 创建日志目录
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 生成日志文件名
    log_file = os.path.join(
        log_dir,
        f"win10_optimize_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('Win10Optimizer')
    logger.info("日志系统初始化完成")
    
    return logger