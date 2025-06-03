# -*- coding: utf-8 -*-
"""
目标检测API模块
处理目标检测相关的API请求
"""

from flask import request, jsonify, current_app
from . import api_bp
from ..services.object_detection_service import ObjectDetectionService
from ..services.opencv_service import OpenCVService
from ..services.yolo_detection_service import YOLODetectionService
from ..utils.helpers import init_gemini_client, save_uploaded_file, allowed_file
import tempfile
import base64
import os



# 延迟初始化服务
def get_object_detection_service(api_key=None):
    """获取目标检测服务实例"""
    try:
        if api_key:
            # 使用用户提供的API key
            from google import genai
            client = genai.Client(api_key=api_key)
        else:
            # 使用默认配置的API key
            client = init_gemini_client()
        return ObjectDetectionService(client)
    except Exception as e:
        current_app.logger.error(f"初始化目标检测服务失败: {e}")
        return None

opencv_service = OpenCVService()
yolo_detection_service = YOLODetectionService()


# 通用的共享文件对象类
class SharedFileObject:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)

    def save(self, path):
        # 检查源文件和目标文件是否相同
        if os.path.abspath(self.filepath) == os.path.abspath(path):
            # 如果是同一个文件，直接返回路径，不需要复制
            return path
        # 复制文件而不是移动
        import shutil
        shutil.copy2(self.filepath, path)
        return path


@api_bp.route('/object-detection', methods=['POST'])
def object_detection():
    """
    目标检测API - Gemini方法

    支持的参数:
    - image: 图像文件
    - object_name: 要检测的对象名称
    """
    try:
        # 获取用户API key
        user_api_key = request.headers.get('X-API-Key')

        # 获取服务实例
        service = get_object_detection_service(api_key=user_api_key)
        if not service:
            return jsonify({
                'success': False,
                'error': '服务初始化失败，请检查API密钥是否正确'
            }), 500

        # 支持JSON和form数据
        if request.is_json:
            data = request.get_json()
            object_name = data.get('object_name', '对象')
            image_data = data.get('image_data')
            result, status_code = service.detect_objects(
                file=None,
                object_name=object_name,
                image_data=image_data
            )
        else:
            file = request.files.get('image')
            object_name = request.form.get('object_name', '对象')

            if not file:
                return jsonify({
                    'success': False,
                    'error': '请上传图像文件'
                }), 400

            result, status_code = service.detect_objects(
                file=file,
                object_name=object_name
            )

        # 对于内容不匹配的情况，返回200状态码让前端正确处理
        if not result.get('success') and (result.get('message') or result.get('suggestion') or result.get('detected_objects') or result.get('explanation')):
            return jsonify(result), 200

        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"目标检测API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'目标检测失败: {str(e)}'
        }), 500


@api_bp.route('/object-detection/opencv', methods=['POST'])
def opencv_detection():
    """OpenCV 目标检测"""
    try:
        # 支持JSON和form数据
        if request.is_json:
            data = request.get_json()
            method = data.get('method', 'contour')
            object_name = data.get('object_name', '对象')
            image_data = data.get('image')
            result, status_code = opencv_service.detect_objects_opencv(
                file=None,
                image_data=image_data,
                method=method,
                object_name=object_name
            )
        else:
            file = request.files.get('image')
            method = request.form.get('method', 'contour')
            object_name = request.form.get('object_name', '对象')
            result, status_code = opencv_service.detect_objects_opencv(
                file=file,
                method=method,
                object_name=object_name
            )

        # 对于内容不匹配的情况，返回200状态码让前端正确处理
        if not result.get('success') and (result.get('message') or result.get('suggestion') or result.get('detected_objects')):
            return jsonify(result), 200

        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"OpenCV检测API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'OpenCV检测失败: {str(e)}'
        }), 500


@api_bp.route('/object-detection/yolo', methods=['POST'])
def yolo_detection():
    """YOLO 目标检测"""
    try:
        # 支持JSON和form数据
        if request.is_json:
            data = request.get_json()
            model_name = data.get('model', 'yolo11n')
            confidence = float(data.get('confidence', 0.5))
            # 支持两种参数名：user_query 和 object_name
            user_query = data.get('user_query', '') or data.get('object_name', '')
            image_data = data.get('image_data')

            # 处理base64图像数据
            if image_data:
                image_data_clean = image_data.split(',')[1] if ',' in image_data else image_data
                image_bytes = base64.b64decode(image_data_clean)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(image_bytes)
                    image_path = tmp_file.name
            else:
                return jsonify({'success': False, 'error': '未提供图像数据'}), 400
        else:
            file = request.files.get('image')
            model_name = request.form.get('model', 'yolo11n')
            confidence = float(request.form.get('confidence', 0.5))
            # 支持两种参数名：user_query 和 object_name
            user_query = request.form.get('user_query', '') or request.form.get('object_name', '')

            if not file:
                return jsonify({'success': False, 'error': '未选择文件'}), 400

            # 保存上传的文件
            if not allowed_file(file.filename):
                return jsonify({'success': False, 'error': '无效的文件类型'}), 400
            image_path = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])

        # 使用YOLO进行检测
        result = yolo_detection_service.detect_objects(image_path, model_name, confidence, user_query)

        # 对于内容不匹配的情况，返回200状态码让前端正确处理
        if not result.get('success') and (result.get('message') or result.get('suggestion') or result.get('detected_objects')):
            return jsonify(result), 200

        return jsonify(result), 200 if result.get('success') else 500

    except Exception as e:
        current_app.logger.error(f"YOLO检测API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'YOLO检测失败: {str(e)}'
        }), 500


@api_bp.route('/object-detection/compare', methods=['POST'])
def compare_detection():
    """对比 Gemini、OpenCV 和 YOLO 的目标检测结果"""
    try:
        # 支持JSON和form数据
        if request.is_json:
            data = request.get_json()
            object_name = data.get('object_name', '对象')
            opencv_method = data.get('opencv_method', 'contour')
            yolo_model = data.get('yolo_model', 'yolo11s')
            image_data = data.get('image_data')

            # 为JSON数据创建共享的临时文件，避免每个服务独立创建导致文件冲突
            # 处理base64图像数据
            image_data_clean = image_data.split(',')[1] if ',' in image_data else image_data
            image_bytes = base64.b64decode(image_data_clean)

            # 创建共享的临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(image_bytes)
                shared_filepath = tmp_file.name

            # 创建共享文件对象
            shared_file = SharedFileObject(shared_filepath)

            try:
                # 获取用户API key
                user_api_key = request.headers.get('X-API-Key')

                # 获取服务实例
                service = get_object_detection_service(api_key=user_api_key)
                if not service:
                    return jsonify({
                        'success': False,
                        'error': '服务初始化失败，请检查API密钥是否正确'
                    }), 500

                # Gemini 检测 - 使用共享文件路径
                gemini_result, _ = service.detect_objects(
                    file=shared_file,
                    object_name=object_name
                )

                # OpenCV 检测 - 使用共享文件路径
                opencv_result, _ = opencv_service.detect_objects_opencv(
                    file=shared_file,
                    method=opencv_method,
                    object_name=object_name
                )

                # YOLO 检测 - 直接使用文件路径
                yolo_result = yolo_detection_service.detect_objects(
                    image_path=shared_filepath,
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
            object_name = request.form.get('object_name', '对象')
            opencv_method = request.form.get('opencv_method', 'contour')
            yolo_model = request.form.get('yolo_model', 'yolo11s')

            # 为表单数据也创建共享文件，避免Flask文件对象只能读取一次的问题
            if not file or file.filename == '':
                return jsonify({'success': False, 'error': '未选择文件'}), 400
            if not allowed_file(file.filename):
                return jsonify({'success': False, 'error': '无效的文件类型'}), 400

            # 保存上传的文件到共享位置
            shared_filepath = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])

            # 创建共享文件对象
            shared_file = SharedFileObject(shared_filepath)

            # 获取用户API key
            user_api_key = request.headers.get('X-API-Key')

            # 获取服务实例
            service = get_object_detection_service(api_key=user_api_key)
            if not service:
                return jsonify({
                    'success': False,
                    'error': '服务初始化失败，请检查API密钥是否正确'
                }), 500

            # Gemini 检测 - 使用共享文件
            gemini_result, _ = service.detect_objects(
                file=shared_file,
                object_name=object_name
            )

            # OpenCV 检测 - 使用共享文件
            opencv_result, _ = opencv_service.detect_objects_opencv(
                file=shared_file,
                method=opencv_method,
                object_name=object_name
            )

            # YOLO 检测 - 直接使用文件路径
            yolo_result = yolo_detection_service.detect_objects(
                image_path=shared_filepath,
                model_name=yolo_model,
                confidence=0.5,
                user_query=object_name
            )

        # 计算检测统计
        gemini_count = len(gemini_result.get('detected_objects', [])) if gemini_result.get('success') else 0
        opencv_count = len(opencv_result.get('detected_objects', [])) if opencv_result.get('success') else 0
        yolo_count = yolo_result.get('total_objects', 0) if yolo_result.get('success') else 0

        # 检查是否至少有一个方法成功检测到对象
        has_successful_detection = gemini_count > 0 or opencv_count > 0 or yolo_count > 0

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
                'has_detections': has_successful_detection
            },
            'object_name': object_name,
            'detection_method': 'comparison'
        }), 200

    except Exception as e:
        current_app.logger.error(f"对比检测API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'对比检测失败: {str(e)}'
        }), 500


@api_bp.route('/object-detection/validate-content', methods=['POST'])
def validate_content_match():
    """验证用户查询与图像内容的匹配性"""
    try:
        file = request.files.get('image')
        user_query = request.form.get('user_query', '')

        if not file:
            return jsonify({'success': False, 'error': '请上传图像文件'}), 400

        if not user_query.strip():
            return jsonify({'success': False, 'error': '请输入查询内容'}), 400

        # 保存上传的图像
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '无效的文件类型'}), 400

        image_path = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])

        # 使用YOLO进行内容匹配验证
        validation_result = yolo_detection_service._validate_content_match(image_path, user_query)

        return jsonify({
            'success': True,
            'validation_result': validation_result
        }), 200

    except Exception as e:
        current_app.logger.error(f"内容匹配验证API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'内容匹配验证失败: {str(e)}'
        }), 500


@api_bp.route('/object-detection/yolo-models', methods=['GET'])
def get_yolo_models():
    """获取可用的YOLO模型列表"""
    try:
        models = yolo_detection_service.get_available_models()
        return jsonify({
            'success': True,
            'models': models
        })
    except Exception as e:
        current_app.logger.error(f"获取YOLO模型列表错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取模型列表失败: {str(e)}'
        }), 500
