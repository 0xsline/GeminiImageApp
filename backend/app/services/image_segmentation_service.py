"""
图像分割服务模块
"""
import os
import json
import tempfile
import base64
from flask import jsonify
from flask import current_app
from ..utils.helpers import save_uploaded_file, image_to_bytes, allowed_file, create_segment_image
from google import genai
from google.genai import types


class ImageSegmentationService:
    def __init__(self, client):
        self.client = client

    def segment_image(self, file=None, object_name='主要对象', image_data=None):
        """分割图像中的对象"""
        try:
            # 处理文件输入
            if image_data:
                # 处理base64图像数据
                image_data_clean = image_data.split(',')[1] if ',' in image_data else image_data
                image_bytes = base64.b64decode(image_data_clean)

                # 创建临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(image_bytes)
                    filepath = tmp_file.name
            else:
                # 处理文件上传
                if not file or file.filename == '':
                    return {'success': False, 'error': '未选择文件'}, 400

                if not allowed_file(file.filename):
                    return {'success': False, 'error': '无效的文件类型'}, 400

                filepath = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])

            if not object_name or not object_name.strip():
                return {'success': False, 'error': '请输入要分割的对象名称'}, 400

            # 读取图像
            image_bytes = image_to_bytes(filepath)

            # 首先验证图像内容是否包含用户查询的对象
            content_validation_prompt = f"""
            请仔细分析这张图像，检查是否包含"{object_name.strip()}"。

            请以JSON格式返回结果：
            {{
                "contains_object": true/false,
                "detected_objects": ["对象1", "对象2", ...],
                "explanation": "详细说明图像中包含什么内容"
            }}

            如果图像中没有"{object_name.strip()}"，请在detected_objects中列出实际检测到的主要对象。
            """

            # 进行内容验证
            validation_response = self.client.models.generate_content(
                model=current_app.config['GEMINI_SEGMENTATION_MODEL'],
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    types.Part.from_text(text=content_validation_prompt)
                ]
            )

            validation_text = validation_response.text.strip()
            validation_data = self._parse_segmentation_response(validation_text)

            # 检查内容匹配性
            if not validation_data.get('contains_object', True):
                detected_objects = validation_data.get('detected_objects', [])
                explanation = validation_data.get('explanation', '图像内容与查询不匹配')

                return {
                    'success': False,
                    'error': f'未检测到目标：{object_name.strip()}',
                    'message': f'图像中检测到的对象与您查询的"{object_name.strip()}"不匹配。{explanation}',
                    'explanation': explanation,
                    'detected_objects': detected_objects,
                    'suggestion': f'图像中包含: {", ".join(detected_objects[:5])}。请修改查询词汇或上传包含"{object_name.strip()}"的图像。' if detected_objects else '请上传包含明确对象的图像，或检查图像质量。',
                    'content_mismatch': True,
                    'user_query': object_name.strip(),
                    'alternative_queries': detected_objects[:3] if detected_objects else []
                }, 200  # 改为200状态码，让前端正确处理内容不匹配

            # 构建分割提示词
            prompt = f"""
            请对图像中的{object_name.strip()}进行分割。
            请识别图像中所有的{object_name.strip()}实例，并为每个实例提供详细的分割信息。

            请以JSON格式返回结果：
            {{
                "segments": [
                    {{
                        "label": "对象标签（如：{object_name}1）",
                        "description": "对象描述",
                        "bbox": [ymin, xmin, ymax, xmax],
                        "confidence": 0.95
                    }}
                ]
            }}

            坐标应该是0到1之间的归一化值。
            请为每个检测到的{object_name.strip()}实例创建一个分割条目。
            如果没有检测到{object_name.strip()}，请返回空的segments数组。
            """

            # 使用 Gemini 进行图像分割
            response = self.client.models.generate_content(
                model=current_app.config['GEMINI_SEGMENTATION_MODEL'],
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    types.Part.from_text(text=prompt)
                ]
            )

            response_text = response.text.strip()

            # 解析分割结果
            segment_data = self._parse_segmentation_response(response_text)

            # 处理分割结果
            segmented_objects = []
            segment_images = []

            segments = segment_data.get('segments', [])
            if not segments and isinstance(segment_data, list):
                segments = segment_data

            for i, segment_info in enumerate(segments):
                label = segment_info.get('label', f'{object_name}_{i+1}')
                description = segment_info.get('description', '')
                bbox = segment_info.get('bbox', [])
                confidence = segment_info.get('confidence', 0.9)

                if len(bbox) == 4:
                    # 创建分割图像（使用边界框裁剪）
                    import time
                    timestamp = int(time.time() * 1000)  # 使用毫秒级时间戳避免重复
                    safe_label = label.replace('/', '_').replace('\\', '_').replace(' ', '_')
                    seg_filename = f"gemini_segment_{safe_label}_{i}_{timestamp}.png"
                    seg_filepath = os.path.join(current_app.config['GENERATED_FOLDER'], seg_filename)

                    # 使用边界框创建分割图像
                    create_segment_image(filepath, bbox, seg_filepath, label)

                    # 使用统一的URL生成函数
                    from ..utils.helpers import get_image_url
                    relative_seg_path = get_image_url(seg_filename, 'generated')
                    segmented_objects.append({
                        'label': label,
                        'description': description,
                        'confidence': confidence,
                        'bbox': bbox,
                        'segment_image': relative_seg_path
                    })
                    segment_images.append(seg_filepath)

            if segmented_objects:
                return {
                    'success': True,
                    'original_image': filepath,
                    'segmented_objects': segmented_objects,
                    'segment_images': segment_images,
                    'response_text': response_text
                }, 200
            else:
                return {
                    'success': False,
                    'error': f'未能分割出{object_name}',
                    'response_text': response_text
                }, 200

        except Exception as e:
            error_msg = f'分割失败: {str(e)}'
            print(f"图像分割错误: {e}")
            return {'success': False, 'error': error_msg}, 500

    def _parse_segmentation_response(self, response_text):
        """解析分割响应"""
        try:
            # 提取JSON部分
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
            else:
                return {"segments": []}

            return json.loads(json_str)

        except (json.JSONDecodeError, ValueError) as e:
            print(f"解析分割响应失败: {e}")
            return {"segments": []}
