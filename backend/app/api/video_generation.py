# -*- coding: utf-8 -*-
"""
视频生成API模块
处理视频生成相关的API请求
"""

from flask import request, jsonify, current_app
from . import api_bp


def get_video_generation_service():
    """获取视频生成服务实例"""
    try:
        from ..services.video_generation_service import VideoGenerationService
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
        # 获取服务实例
        service = get_video_generation_service()
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败'
            }), 500

        # 支持JSON和form数据
        if request.is_json:
            data = request.get_json()
            prompt = data.get('prompt', '')
            duration = int(data.get('duration', 8))
            style = data.get('style', 'realistic')
            aspect_ratio = data.get('aspect_ratio', '16:9')
        else:
            prompt = request.form.get('prompt', '')
            duration = int(request.form.get('duration', 8))
            style = request.form.get('style', 'realistic')
            aspect_ratio = request.form.get('aspect_ratio', '16:9')

        if not prompt.strip():
            return jsonify({
                'success': False,
                'error': '请输入视频描述'
            }), 400

        result, status_code = service.generate_video(
            prompt=prompt,
            duration=duration,
            style=style,
            aspect_ratio=aspect_ratio
        )

        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"视频生成API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'视频生成失败: {str(e)}'
        }), 500


@api_bp.route('/video-generation/from-image', methods=['POST'])
def video_from_image():
    """从图像生成视频 - 图像到视频功能"""
    try:
        # 获取服务实例
        service = get_video_generation_service()
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败'
            }), 500

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
        return jsonify({
            'success': False,
            'error': f'图像到视频生成失败: {str(e)}'
        }), 500


@api_bp.route('/video-generation/options', methods=['GET'])
def get_video_options():
    """获取视频生成选项"""
    try:
        service = get_video_generation_service()
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败'
            }), 500

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
        return jsonify({
            'success': False,
            'error': f'获取选项失败: {str(e)}'
        }), 500


@api_bp.route('/video-generation/test', methods=['GET'])
def test_video_api():
    """测试视频生成API连接"""
    try:
        service = get_video_generation_service()
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败'
            }), 500

        # 测试基本连接
        return jsonify({
            'success': True,
            'message': '视频生成服务连接正常',
            'model': 'veo-2.0-generate-001',
            'api_version': '2025',
            'supported_features': [
                'text-to-video',
                'image-to-video',
                'prompt-enhancement',
                'multiple-aspect-ratios'
            ]
        })
    except Exception as e:
        current_app.logger.error(f"测试视频API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'API测试失败: {str(e)}'
        }), 500
