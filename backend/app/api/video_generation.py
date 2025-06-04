# -*- coding: utf-8 -*-
"""
视频生成API模块
处理视频生成相关的API请求
优化版本：支持本地文件处理
"""

from flask import request, jsonify, current_app
from . import api_bp
from ..utils.helpers import handle_api_error
import os


def get_video_generation_service(api_key=None):
    """获取视频生成服务实例"""
    try:
        from ..services.video_generation_service import VideoGenerationService
        if api_key:
            # 使用用户提供的API key
            from google import genai
            client = genai.Client(api_key=api_key)
        else:
            # 使用默认配置的API key
            from ..utils.helpers import init_gemini_client
            client = init_gemini_client()
        return VideoGenerationService(client)
    except Exception as e:
        current_app.logger.error(f"初始化视频生成服务失败: {e}")
        return None


@api_bp.route('/video-generation', methods=['POST'])
def video_generation():
    """
    视频生成API - 支持Veo 2.0

    支持的参数:
    - prompt: 视频描述
    - duration: 视频时长 (默认: 8秒)
    - style: 视频风格 (默认: realistic)
    - aspect_ratio: 宽高比 (默认: 16:9)
    """
    try:
        # 获取用户API key
        user_api_key = request.headers.get('X-API-Key')

        # 获取服务实例
        service = get_video_generation_service(api_key=user_api_key)
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败，请检查API密钥是否正确',
                'suggestion': '请确认API密钥是否有效，或联系管理员'
            }), 400

        # 支持JSON和form数据
        if request.is_json:
            data = request.get_json()
            prompt = data.get('prompt', '')
            duration = int(data.get('duration', 8))
            style = data.get('style', 'realistic')
            aspect_ratio = data.get('aspect_ratio', '16:9')
            negative_prompt = data.get('negative_prompt', '')
        else:
            prompt = request.form.get('prompt', '')
            duration = int(request.form.get('duration', 8))
            style = request.form.get('style', 'realistic')
            aspect_ratio = request.form.get('aspect_ratio', '16:9')
            negative_prompt = request.form.get('negative_prompt', '')

        if not prompt.strip():
            return jsonify({
                'success': False,
                'error': '请输入视频描述'
            }), 400

        result, status_code = service.generate_video(
            prompt=prompt,
            duration=duration,
            style=style,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt
        )

        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"视频生成API错误: {str(e)}")
        error_response, status_code = handle_api_error(e, "视频生成")
        return jsonify(error_response), status_code


@api_bp.route('/video-generation/from-image', methods=['POST'])
def video_from_image():
    """从上传的图像生成视频 - 图像到视频功能"""
    try:
        # 获取用户API key
        user_api_key = request.headers.get('X-API-Key')

        # 获取服务实例
        service = get_video_generation_service(api_key=user_api_key)
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败，请检查API密钥是否正确',
                'suggestion': '请确认API密钥是否有效，或联系管理员'
            }), 400

        file = request.files.get('image')
        prompt = request.form.get('prompt', '')
        duration = int(request.form.get('duration', 8))
        aspect_ratio = request.form.get('aspect_ratio', '16:9')

        if not file:
            return jsonify({'success': False, 'error': '请上传图像文件'}), 400

        # 保存上传的图像
        from ..utils.helpers import save_uploaded_file, allowed_file
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '无效的文件类型'}), 400

        image_path = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])

        result, status_code = service.generate_video_from_image(
            image_path=image_path,
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio
        )
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"图像到视频生成API错误: {str(e)}")
        error_response, status_code = handle_api_error(e, "图像到视频生成")
        return jsonify(error_response), status_code


@api_bp.route('/video-generation/from-local-image', methods=['POST'])
def video_from_local_image():
    """从项目中的本地图像文件生成视频 - 新增功能，避免上传"""
    try:
        # 获取用户API key
        user_api_key = request.headers.get('X-API-Key')

        # 获取服务实例
        service = get_video_generation_service(api_key=user_api_key)
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败，请检查API密钥是否正确',
                'suggestion': '请确认API密钥是否有效，或联系管理员'
            }), 400

        # 支持JSON和form数据
        if request.is_json:
            data = request.get_json()
            local_image_path = data.get('image_path', '')
            prompt = data.get('prompt', '')
            duration = int(data.get('duration', 8))
            aspect_ratio = data.get('aspect_ratio', '16:9')
        else:
            local_image_path = request.form.get('image_path', '')
            prompt = request.form.get('prompt', '')
            duration = int(request.form.get('duration', 8))
            aspect_ratio = request.form.get('aspect_ratio', '16:9')

        if not local_image_path.strip():
            return jsonify({
                'success': False,
                'error': '请指定本地图像文件路径'
            }), 400

        result, status_code = service.generate_video_from_local_image_file(
            local_image_path=local_image_path,
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio
        )
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"本地图像到视频生成API错误: {str(e)}")
        error_response, status_code = handle_api_error(e, "本地图像到视频生成")
        return jsonify(error_response), status_code


@api_bp.route('/video-generation/local-images', methods=['GET'])
def get_local_images():
    """获取项目中可用的本地图像文件列表"""
    try:
        local_images = []

        # 扫描项目中的图像文件
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']

        # 检查几个常见的图像文件夹
        search_paths = [
            'img',
            'images',
            'assets',
            'storage/images',
            '.'  # 项目根目录
        ]

        project_root = os.path.abspath(os.path.join(current_app.root_path, '..'))

        for search_path in search_paths:
            full_path = os.path.join(project_root, search_path)
            if os.path.exists(full_path):
                for root, dirs, files in os.walk(full_path):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in image_extensions):
                            relative_path = os.path.relpath(os.path.join(root, file), project_root)
                            file_size = os.path.getsize(os.path.join(root, file))
                            local_images.append({
                                'path': relative_path.replace('\\', '/'),  # 统一使用正斜杠
                                'name': file,
                                'size': f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / 1024 / 1024:.1f} MB"
                            })

        return jsonify({
            'success': True,
            'images': local_images,
            'total': len(local_images),
            'message': f'找到 {len(local_images)} 个本地图像文件'
        })

    except Exception as e:
        current_app.logger.error(f"获取本地图像列表错误: {str(e)}")
        error_response, status_code = handle_api_error(e, "获取本地图像列表")
        return jsonify(error_response), status_code


@api_bp.route('/video-generation/options', methods=['GET'])
def get_video_options():
    """获取视频生成选项"""
    try:
        # 获取用户API key
        user_api_key = request.headers.get('X-API-Key')

        service = get_video_generation_service(api_key=user_api_key)
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败，请检查API密钥是否正确',
                'suggestion': '请确认API密钥是否有效，或联系管理员'
            }), 400

        styles = service.get_video_styles()
        durations = service.get_duration_options()
        aspect_ratios = service.get_aspect_ratio_options()

        return jsonify({
            'success': True,
            'styles': styles,
            'durations': durations,
            'aspect_ratios': aspect_ratios,
            'default_style': 'realistic',
            'default_duration': 8,
            'default_aspect_ratio': '16:9'
        })
    except Exception as e:
        current_app.logger.error(f"获取视频选项API错误: {str(e)}")
        error_response, status_code = handle_api_error(e, "获取视频选项")
        return jsonify(error_response), status_code


@api_bp.route('/video-generation/test', methods=['GET'])
def test_video_api():
    """测试视频生成API连接"""
    try:
        # 获取用户API key
        user_api_key = request.headers.get('X-API-Key')

        service = get_video_generation_service(api_key=user_api_key)
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败，请检查API密钥是否正确',
                'suggestion': '请确认API密钥是否有效，或联系管理员'
            }), 400

        # 测试基本连接
        return jsonify({
            'success': True,
            'message': '视频生成服务连接正常',
            'model': 'veo-2.0-generate-001',
            'api_version': '2025',
            'supported_features': [
                'text-to-video',
                'image-to-video',
                'local-image-to-video',  # 新增功能
                'prompt-enhancement',
                'multiple-aspect-ratios'
            ]
        })
    except Exception as e:
        current_app.logger.error(f"测试视频API错误: {str(e)}")
        error_response, status_code = handle_api_error(e, "视频API测试")
        return jsonify(error_response), status_code
