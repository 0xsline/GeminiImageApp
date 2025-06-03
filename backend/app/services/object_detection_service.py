"""
目标检测服务模块
"""
import os
import json
import re
import tempfile
import base64
from flask import jsonify
from flask import current_app
from ..utils.helpers import save_uploaded_file, image_to_bytes, allowed_file, draw_bounding_box, draw_all_bounding_boxes
from google import genai
from google.genai import types


class ObjectDetectionService:
    def __init__(self, client):
        self.client = client

    def detect_objects(self, file=None, object_name='对象', image_data=None):
        """检测图像中的对象"""
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
                return {'success': False, 'error': '请输入要检测的对象名称'}, 400

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
                model=current_app.config['GEMINI_VISION_MODEL'],
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    types.Part.from_text(text=content_validation_prompt)
                ]
            )

            validation_text = validation_response.text.strip()
            validation_data = self._parse_detection_response(validation_text, "validation")

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

            # 构建检测提示词
            prompt = f"""
            请检测图像中的{object_name.strip()}，并返回边界框坐标。
            请以JSON格式返回结果，包含以下信息：
            {{
                "objects": [
                    {{
                        "label": "对象标签",
                        "confidence": 0.95,
                        "bbox": [ymin, xmin, ymax, xmax]
                    }}
                ]
            }}
            坐标应该是0到1之间的归一化值。
            如果没有检测到{object_name.strip()}，请返回空的objects数组。
            """

            # 使用 Gemini 进行目标检测
            response = self.client.models.generate_content(
                model=current_app.config['GEMINI_VISION_MODEL'],
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    types.Part.from_text(text=prompt)
                ]
            )

            response_text = response.text.strip()

            # 解析检测结果
            detection_data = self._parse_detection_response(response_text, object_name)

            # 处理检测到的对象
            detected_objects = []
            bbox_images = []

            for i, obj in enumerate(detection_data.get('objects', [])):
                bbox = obj.get('bbox', [])
                label = obj.get('label', object_name)
                confidence = obj.get('confidence', 0.9)

                if len(bbox) == 4:
                    # 在图像上绘制边界框
                    bbox_filename = f"bbox_{label}_{i}_{os.path.basename(filepath)}"
                    bbox_filepath = os.path.join(current_app.config['GENERATED_FOLDER'], bbox_filename)
                    draw_bounding_box(filepath, bbox, bbox_filepath, label=label)

                    detected_objects.append({
                        'label': label,
                        'confidence': confidence,
                        'bbox': bbox
                    })
                    bbox_images.append(bbox_filepath)

            if detected_objects:
                # 创建汇总图片，将所有检测到的对象绘制在一张图上
                summary_filename = f"summary_all_objects_{os.path.basename(filepath)}"
                summary_filepath = os.path.join(current_app.config['GENERATED_FOLDER'], summary_filename)
                draw_all_bounding_boxes(filepath, detected_objects, summary_filepath)

                # 使用统一的URL生成函数
                from ..utils.helpers import get_image_url
                relative_bbox_images = [get_image_url(os.path.basename(img), 'generated') for img in bbox_images]
                relative_summary_image = get_image_url(os.path.basename(summary_filepath), 'generated')

                return {
                    'success': True,
                    'detected_objects': detected_objects,
                    'original_image': filepath,
                    'bbox_images': relative_bbox_images,
                    'summary_image': relative_summary_image,  # 新增汇总图片
                    'response_text': response_text
                }, 200
            else:
                return {
                    'success': False,
                    'error': f'未检测到{object_name}',
                    'response_text': response_text
                }, 200

        except Exception as e:
            error_msg = f'检测失败: {str(e)}'
            print(f"目标检测错误: {e}")
            return {'success': False, 'error': error_msg}, 500

    def _parse_detection_response(self, response_text, object_name):
        """解析检测响应"""
        try:
            # 提取JSON部分
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
            else:
                # 尝试提取简单的坐标格式
                coords_match = re.search(r'\[([\d\.,\s]+)\]', response_text)
                if coords_match:
                    coords_str = coords_match.group(1)
                    coords = [float(x.strip()) for x in coords_str.split(',')]
                    return {
                        "objects": [{
                            "label": object_name,
                            "confidence": 0.9,
                            "bbox": coords
                        }]
                    }
                else:
                    return {"objects": []}

            return json.loads(json_str)

        except (json.JSONDecodeError, ValueError) as e:
            print(f"解析检测响应失败: {e}")
            return {"objects": []}
