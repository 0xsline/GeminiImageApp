# -*- coding: utf-8 -*-
"""
API蓝图模块
包含所有API路由的注册
"""

from flask import Blueprint

# 创建API蓝图
api_bp = Blueprint('api', __name__)

# 导入基本API路由
try:
    from . import utils
    print("✅ 基本API模块导入成功")
except ImportError as e:
    # 如果某些模块导入失败，记录错误但不中断应用启动
    import logging
    logging.warning(f"基本API模块导入失败: {e}")

# 尝试导入其他API路由（可选）
try:
    from . import image_qa
    print("✅ 图像问答API模块导入成功")
except ImportError as e:
    import logging
    logging.warning(f"图像问答API模块导入失败: {e}")

try:
    from . import image_generation
    print("✅ 图像生成API模块导入成功")
except ImportError as e:
    import logging
    logging.warning(f"图像生成API模块导入失败: {e}")

try:
    from . import image_editing
    print("✅ 图像编辑API模块导入成功")
except ImportError as e:
    import logging
    logging.warning(f"图像编辑API模块导入失败: {e}")

try:
    from . import object_detection
    print("✅ 目标检测API模块导入成功")
except ImportError as e:
    import logging
    logging.warning(f"目标检测API模块导入失败: {e}")

try:
    from . import image_segmentation
    print("✅ 图像分割API模块导入成功")
except ImportError as e:
    import logging
    logging.warning(f"图像分割API模块导入失败: {e}")

try:
    from . import video_generation
    print("✅ 视频生成API模块导入成功")
except ImportError as e:
    import logging
    logging.warning(f"视频生成API模块导入失败: {e}")
