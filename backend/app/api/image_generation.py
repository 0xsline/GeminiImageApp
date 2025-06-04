# -*- coding: utf-8 -*-
"""
图像生成API模块
处理图像生成相关的API请求
"""

from flask import request, jsonify, current_app
from . import api_bp
from ..services.image_generation_service import ImageGenerationService
from ..utils.helpers import init_gemini_client, handle_api_error


# 延迟初始化服务
def get_image_generation_service(api_key=None):
    """获取图像生成服务实例"""
    try:
        if api_key:
            # 使用用户提供的API key
            from google import genai
            client = genai.Client(api_key=api_key)
        else:
            # 使用默认配置的API key
            client = init_gemini_client()
        return ImageGenerationService(client)
    except Exception as e:
        current_app.logger.error(f"初始化图像生成服务失败: {e}")
        return None


@api_bp.route('/image-generation', methods=['POST'])
def image_generation():
    """
    图像生成API

    支持的参数:
    - prompt: 文本描述
    - model: 生成模型 (默认: imagen-3.0-generate-002)
    - aspect_ratio: 宽高比 (默认: 1:1)
    - style: 风格 (默认: realistic)
    """
    try:
        # 获取用户API key
        user_api_key = request.headers.get('X-API-Key')

        # 获取服务实例
        service = get_image_generation_service(api_key=user_api_key)
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
            model_type = data.get('model', 'imagen-3.0-generate-002')
            aspect_ratio = data.get('aspect_ratio', '1:1')
            style = data.get('style', 'realistic')
        else:
            prompt = request.form.get('prompt', '')
            model_type = request.form.get('model', 'imagen-3.0-generate-002')
            aspect_ratio = request.form.get('aspect_ratio', '1:1')
            style = request.form.get('style', 'realistic')

        if not prompt.strip():
            return jsonify({
                'success': False,
                'error': '请输入图像描述'
            }), 400

        result, status_code = service.generate_image(
            prompt, model_type, aspect_ratio, style
        )
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"图像生成API错误: {str(e)}")
        error_response, status_code = handle_api_error(e, "图像生成")
        return jsonify(error_response), status_code


@api_bp.route('/image-generation/models', methods=['GET'])
def get_image_generation_models():
    """获取可用的图像生成模型列表"""
    try:
        service = get_image_generation_service()
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败，请检查API密钥是否正确',
                'suggestion': '请确认API密钥是否有效，或联系管理员'
            }), 400

        models = service.get_model_options()
        return jsonify({
            'success': True,
            'models': models,
            'default_model': 'imagen-3.0-generate-002'
        })
    except Exception as e:
        current_app.logger.error(f"获取生成模型列表错误: {str(e)}")
        error_response, status_code = handle_api_error(e, "获取模型列表")
        return jsonify(error_response), status_code


@api_bp.route('/image-generation/options', methods=['GET'])
def get_image_generation_options():
    """获取图像生成选项"""
    try:
        service = get_image_generation_service()
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败'
            }), 500

        styles = service.get_image_styles()
        ratios = service.get_aspect_ratio_options()
        models = service.get_model_options()

        return jsonify({
            'success': True,
            'styles': styles,
            'aspect_ratios': ratios,
            'models': models,
            'default_style': 'realistic',
            'default_aspect_ratio': '1:1',
            'default_model': 'imagen-3.0-generate-002'
        })
    except Exception as e:
        current_app.logger.error(f"获取生成选项错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取选项失败: {str(e)}'
        }), 500


@api_bp.route('/image-editing/advanced', methods=['POST'])
def image_editing_advanced():
    """高级图像编辑功能"""
    try:
        file = request.files.get('image')
        edit_prompt = request.form.get('edit_prompt', '')
        mask_file = request.files.get('mask')

        if not file:
            return jsonify({'success': False, 'error': '请上传图像文件'}), 400

        if not edit_prompt.strip():
            return jsonify({'success': False, 'error': '请输入编辑指令'}), 400

        # 保存上传的图像
        from ..utils.helpers import save_uploaded_file, allowed_file
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '无效的文件类型'}), 400

        image_path = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])

        # 保存遮罩文件（如果有）
        mask_path = None
        if mask_file and allowed_file(mask_file.filename):
            mask_path = save_uploaded_file(mask_file, current_app.config['UPLOAD_FOLDER'])

        # 使用Imagen 3.0进行图像编辑
        service = get_image_generation_service()
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败'
            }), 500

        result, status_code = service.edit_image(
            image_path=image_path,
            edit_prompt=edit_prompt,
            mask_path=mask_path
        )

        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"高级图像编辑错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'高级图像编辑失败: {str(e)}'
        }), 500


@api_bp.route('/image-upscale', methods=['POST'])
def image_upscale():
    """图像放大功能"""
    try:
        file = request.files.get('image')
        scale_factor = int(request.form.get('scale_factor', 2))

        if not file:
            return jsonify({'success': False, 'error': '请上传图像文件'}), 400

        if scale_factor < 1 or scale_factor > 4:
            return jsonify({'success': False, 'error': '放大倍数必须在1-4之间'}), 400

        # 保存上传的图像
        from ..utils.helpers import save_uploaded_file, allowed_file
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '无效的文件类型'}), 400

        image_path = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])

        # 使用图像放大功能
        service = get_image_generation_service()
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败'
            }), 500

        result, status_code = service.upscale_image(
            image_path=image_path,
            scale_factor=scale_factor
        )

        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"图像放大错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'图像放大失败: {str(e)}'
        }), 500
