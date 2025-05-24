# -*- coding: utf-8 -*-
"""
应用配置管理
包含不同环境的配置类
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """基础配置类"""

    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # API配置
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')

    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'storage', 'uploads')
    GENERATED_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'storage', 'generated')
    MODELS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'storage', 'models')

    # 文件大小限制 (16MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

    # Gemini模型配置
    DEFAULT_VISION_MODEL = 'gemini-2.0-flash'
    DEFAULT_GENERATION_MODEL = 'imagen-3.0-generate-002'
    GEMINI_VISION_MODEL = "gemini-2.0-flash"  # 用于视觉任务
    GEMINI_IMAGE_GEN_MODEL = "gemini-2.0-flash-exp-image-generation"  # 图像生成
    IMAGEN_MODEL = "imagen-3.0-generate-002"  # Imagen 3 图像生成
    GEMINI_SEGMENTATION_MODEL = "gemini-2.0-flash"  # 用于分割任务，避免配额问题

    # 支持的图像生成模型映射
    SUPPORTED_IMAGE_MODELS = {
        'imagen-3': 'imagen-3.0-generate-002',
        'gemini-2.0-flash': 'gemini-2.0-flash-exp-image-generation'
    }

    # 应用设置
    JSON_AS_ASCII = False  # 支持中文JSON响应

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保必要的目录存在
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)
        os.makedirs(app.config['MODELS_FOLDER'], exist_ok=True)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
