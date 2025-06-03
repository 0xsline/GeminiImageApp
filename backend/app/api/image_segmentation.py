# -*- coding: utf-8 -*-
"""
图像分割API模块
处理图像分割相关的API请求
"""

from flask import request, jsonify, current_app
from . import api_bp
import tempfile
import base64
import os


def get_segmentation_services(api_key=None):
    """获取图像分割服务实例"""
    try:
        from ..services.image_segmentation_service import ImageSegmentationService
        from ..services.opencv_service import OpenCVService
        from ..services.yolo_segmentation_service import YOLOSegmentationService
        from ..utils.helpers import init_gemini_client

        if api_key:
            # 使用用户提供的API key
            from google import genai
            client = genai.Client(api_key=api_key)
        else:
            # 使用默认配置的API key
            client = init_gemini_client()

        return {
            'gemini': ImageSegmentationService(client),
            'opencv': OpenCVService(),
            'yolo': YOLOSegmentationService()
        }
    except Exception as e:
        current_app.logger.error(f"初始化图像分割服务失败: {e}")
        return None


# 通用的共享文件对象类
class SharedFileObject:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)

    def save(self, path):
        # 检查源文件和目标文件是否相同
        if os.path.abspath(self.filepath) == os.path.abspath(path):
            return path
        # 复制文件而不是移动
        import shutil
        shutil.copy2(self.filepath, path)
        return path


@api_bp.route('/image-segmentation', methods=['POST'])
def image_segmentation():
    """
    图像分割API - Gemini方法

    支持的参数:
    - image: 图像文件
    - object_name: 要分割的对象名称
    """
    try:
        # 获取用户API key
        user_api_key = request.headers.get('X-API-Key')

        # 获取服务实例
        services = get_segmentation_services(api_key=user_api_key)
        if not services:
            return jsonify({
                'success': False,
                'error': '服务初始化失败，请检查API密钥是否正确'
            }), 500

        # 支持JSON和form数据
        if request.is_json:
            data = request.get_json()
            object_name = data.get('object_name', '')
            image_data = data.get('image_data')
            result, status_code = services['gemini'].segment_image(
                file=None,
                object_name=object_name,
                image_data=image_data
            )
        else:
            file = request.files.get('image')
            object_name = request.form.get('object_name', '')

            if not file:
                return jsonify({
                    'success': False,
                    'error': '请上传图像文件'
                }), 400

            result, status_code = services['gemini'].segment_image(
                file=file,
                object_name=object_name
            )

        # 对于内容不匹配的情况，返回200状态码让前端正确处理
        if not result.get('success') and (result.get('message') or result.get('suggestion') or result.get('detected_objects') or result.get('explanation') or result.get('content_mismatch')):
            return jsonify(result), 200

        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"图像分割API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'图像分割失败: {str(e)}'
        }), 500


@api_bp.route('/image-segmentation/opencv', methods=['POST'])
def opencv_segmentation():
    """OpenCV 图像分割"""
    try:
        # 获取用户API key
        user_api_key = request.headers.get('X-API-Key')

        # 获取服务实例
        services = get_segmentation_services(api_key=user_api_key)
        if not services:
            return jsonify({
                'success': False,
                'error': '服务初始化失败，请检查API密钥是否正确'
            }), 500

        # 支持JSON和form数据
        if request.is_json:
            data = request.get_json()
            method = data.get('method', 'contour_mask')
            object_name = data.get('object_name', '')
            image_data = data.get('image_data')
            result, status_code = services['opencv'].segment_image_opencv(
                file=None,
                image_data=image_data,
                method=method,
                object_name=object_name
            )
        else:
            file = request.files.get('image')
            method = request.form.get('method', 'contour_mask')
            object_name = request.form.get('object_name', '')
            result, status_code = services['opencv'].segment_image_opencv(
                file=file,
                method=method,
                object_name=object_name
            )

        # 对于内容不匹配的情况，返回200状态码让前端正确处理
        if not result.get('success') and (result.get('message') or result.get('suggestion') or result.get('detected_objects') or result.get('explanation') or result.get('content_mismatch')):
            return jsonify(result), 200

        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"OpenCV分割API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'OpenCV分割失败: {str(e)}'
        }), 500


@api_bp.route('/image-segmentation/yolo', methods=['POST'])
def yolo_segmentation():
    """YOLO 图像分割"""
    try:
        # 获取用户API key
        user_api_key = request.headers.get('X-API-Key')

        # 获取服务实例
        services = get_segmentation_services(api_key=user_api_key)
        if not services:
            return jsonify({
                'success': False,
                'error': '服务初始化失败，请检查API密钥是否正确'
            }), 500

        # 支持JSON和form数据
        if request.is_json:
            data = request.get_json()
            model_name = data.get('model_name', 'yolo11n-seg')
            confidence = float(data.get('confidence', 0.5))
            user_query = data.get('user_query', '')
            image_data = data.get('image_data')
            result, status_code = services['yolo'].segment_image_yolo(
                file=None,
                image_data=image_data,
                model_name=model_name,
                confidence=confidence,
                user_query=user_query
            )
        else:
            file = request.files.get('image')
            model_name = request.form.get('model_name', 'yolo11n-seg')
            confidence = float(request.form.get('confidence', 0.5))
            user_query = request.form.get('user_query', '')
            result, status_code = services['yolo'].segment_image_yolo(
                file=file,
                model_name=model_name,
                confidence=confidence,
                user_query=user_query
            )

        # 对于内容不匹配的情况，返回200状态码让前端正确处理
        if not result.get('success') and (result.get('message') or result.get('suggestion') or result.get('detected_objects') or result.get('explanation') or result.get('content_mismatch')):
            return jsonify(result), 200

        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"YOLO分割API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'YOLO分割失败: {str(e)}'
        }), 500


@api_bp.route('/image-segmentation/compare', methods=['POST'])
def compare_segmentation():
    """对比 Gemini、OpenCV 和 YOLO 的图像分割结果"""
    try:
        # 获取用户API key
        user_api_key = request.headers.get('X-API-Key')

        # 获取服务实例
        services = get_segmentation_services(api_key=user_api_key)
        if not services:
            return jsonify({
                'success': False,
                'error': '服务初始化失败，请检查API密钥是否正确'
            }), 500

        # 支持JSON和form数据
        if request.is_json:
            data = request.get_json()
            object_name = data.get('object_name', '主要对象')
            opencv_method = data.get('opencv_method', 'grabcut')
            yolo_model = data.get('yolo_model', 'yolo11n-seg')
            image_data = data.get('image_data')

            # 为JSON数据创建共享的临时文件
            image_data_clean = image_data.split(',')[1] if ',' in image_data else image_data
            image_bytes = base64.b64decode(image_data_clean)

            # 创建共享的临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(image_bytes)
                shared_filepath = tmp_file.name

            # 创建共享文件对象
            shared_file = SharedFileObject(shared_filepath)

            try:
                # Gemini 分割
                gemini_result, _ = services['gemini'].segment_image(
                    file=shared_file,
                    object_name=object_name
                )

                # OpenCV 分割
                opencv_result, _ = services['opencv'].segment_image_opencv(
                    file=shared_file,
                    method=opencv_method
                )

                # YOLO 分割
                yolo_result, _ = services['yolo'].segment_image_yolo(
                    file=None,
                    image_data=image_data,
                    model_name=yolo_model,
                    confidence=0.5,
                    user_query=object_name
                )

            finally:
                # 清理共享的临时文件
                try:
                    os.unlink(shared_filepath)
                except:
                    pass
        else:
            file = request.files.get('image')
            object_name = request.form.get('object_name', '主要对象')
            opencv_method = request.form.get('opencv_method', 'grabcut')
            yolo_model = request.form.get('yolo_model', 'yolo11n-seg')

            if not file or file.filename == '':
                return jsonify({'success': False, 'error': '未选择文件'}), 400

            from ..utils.helpers import save_uploaded_file, allowed_file
            if not allowed_file(file.filename):
                return jsonify({'success': False, 'error': '无效的文件类型'}), 400

            # 保存上传的文件到共享位置
            shared_filepath = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])

            # 创建共享文件对象
            shared_file = SharedFileObject(shared_filepath)

            # Gemini 分割
            gemini_result, _ = services['gemini'].segment_image(
                file=shared_file,
                object_name=object_name
            )

            # OpenCV 分割
            opencv_result, _ = services['opencv'].segment_image_opencv(
                file=shared_file,
                method=opencv_method,
                object_name=object_name
            )

            # YOLO 分割
            yolo_result, _ = services['yolo'].segment_image_yolo(
                file=shared_file,
                model_name=yolo_model,
                confidence=0.5,
                user_query=object_name
            )

        # 计算分割统计
        gemini_count = len(gemini_result.get('segmented_objects', [])) if gemini_result.get('success') else 0
        opencv_count = len(opencv_result.get('segmented_objects', [])) if opencv_result.get('success') else 0
        yolo_count = len(yolo_result.get('segmented_objects', [])) if yolo_result.get('success') else 0

        # 检查是否至少有一个方法成功分割到对象
        has_successful_segmentation = gemini_count > 0 or opencv_count > 0 or yolo_count > 0

        return jsonify({
            'success': True,
            'gemini_result': gemini_result,
            'opencv_result': opencv_result,
            'yolo_result': yolo_result,
            'comparison': {
                'gemini_count': gemini_count,
                'opencv_count': opencv_count,
                'yolo_count': yolo_count,
                'total_methods': 3,
                'successful_methods': sum([1 for result in [gemini_result, opencv_result, yolo_result] if result.get('success')]),
                'has_segmentations': has_successful_segmentation
            },
            'object_name': object_name,
            'segmentation_method': 'comparison'
        }), 200

    except Exception as e:
        current_app.logger.error(f"对比分割API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'对比分割失败: {str(e)}'
        }), 500


@api_bp.route('/image-segmentation/yolo-models', methods=['GET'])
def get_yolo_segmentation_models():
    """获取可用的YOLO分割模型列表"""
    try:
        # 获取用户API key
        user_api_key = request.headers.get('X-API-Key')

        services = get_segmentation_services(api_key=user_api_key)
        if not services:
            return jsonify({
                'success': False,
                'error': '服务初始化失败，请检查API密钥是否正确'
            }), 500

        models = services['yolo'].get_available_models()
        return jsonify({
            'success': True,
            'models': models
        })
    except Exception as e:
        current_app.logger.error(f"获取YOLO分割模型列表错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取模型列表失败: {str(e)}'
        }), 500
