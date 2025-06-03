# -*- coding: utf-8 -*-
"""
图像问答API模块
处理图像问答相关的API请求
"""

from flask import request, jsonify, current_app
from . import api_bp
from ..services.image_qa_service import ImageQAService
from ..utils.helpers import init_gemini_client


# 延迟初始化服务
def get_image_qa_service(api_key=None):
    """获取图像问答服务实例"""
    try:
        if api_key:
            # 使用用户提供的API key
            from google import genai
            client = genai.Client(api_key=api_key)
        else:
            # 使用默认配置的API key
            client = init_gemini_client()
        return ImageQAService(client)
    except Exception as e:
        current_app.logger.error(f"初始化图像问答服务失败: {e}")
        return None


@api_bp.route('/image-qa', methods=['POST'])
def image_qa():
    """
    图像问答API

    支持的参数:
    - image: 图像文件
    - question: 问题文本
    - model: 使用的模型 (默认: gemini-2.0-flash)
    """
    try:
        # 获取用户API key
        user_api_key = request.headers.get('X-API-Key')

        # 获取服务实例
        service = get_image_qa_service(api_key=user_api_key)
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败，请检查API密钥是否正确'
            }), 500

        # 支持JSON和form数据
        if request.is_json:
            data = request.get_json()
            question = data.get('question', '')
            model = data.get('model', 'gemini-2.0-flash')
            image_data = data.get('image_data')

            result, status_code = service.process_image_qa(
                file=None,
                question=question,
                model=model,
                image_data=image_data
            )
        else:
            file = request.files.get('image')
            question = request.form.get('question', '')
            model = request.form.get('model', 'gemini-2.0-flash')

            if not file:
                return jsonify({
                    'success': False,
                    'error': '请上传图像文件'
                }), 400

            if not question.strip():
                return jsonify({
                    'success': False,
                    'error': '请输入问题'
                }), 400

            result, status_code = service.process_image_qa(
                file=file,
                question=question,
                model=model
            )

        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"图像问答API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'处理失败: {str(e)}'
        }), 500


@api_bp.route('/image-qa/models', methods=['GET'])
def get_image_qa_models():
    """获取可用的图像问答模型列表"""
    try:
        models = {
            'gemini-2.0-flash': {
                'name': 'Gemini 2.0 Flash',
                'description': '最新的多模态模型，支持图像、文本、音频和视频',
                'recommended': True
            },
            'gemini-1.5-flash': {
                'name': 'Gemini 1.5 Flash',
                'description': '快速的多模态模型，适合实时应用'
            },
            'gemini-1.5-pro': {
                'name': 'Gemini 1.5 Pro',
                'description': '高性能的多模态模型，适合复杂任务'
            },
            'gemini-2.5-pro-exp-03-25': {
                'name': 'Gemini 2.5 Pro Experimental',
                'description': '实验性的高级模型，具有最新功能',
                'experimental': True
            }
        }

        return jsonify({
            'success': True,
            'models': models,
            'default_model': 'gemini-2.0-flash'
        })

    except Exception as e:
        current_app.logger.error(f"获取模型列表错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取模型列表失败: {str(e)}'
        }), 500
