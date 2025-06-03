"""
图像编辑服务模块
"""
import os
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import tempfile
import base64
from flask import current_app
from ..utils.helpers import save_uploaded_file, allowed_file
from google import genai
from google.genai import types


class ImageEditingService:
    def __init__(self, client):
        self.client = client

    def edit_image(self, file=None, image_data=None, edit_type='gemini', edit_params=None):
        """图像编辑主函数"""
        try:
            # 处理文件输入
            if image_data:
                image_data_clean = image_data.split(',')[1] if ',' in image_data else image_data
                image_bytes = base64.b64decode(image_data_clean)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(image_bytes)
                    filepath = tmp_file.name
            else:
                if not file or file.filename == '':
                    return {'success': False, 'error': '未选择文件'}, 400
                if not allowed_file(file.filename):
                    return {'success': False, 'error': '无效的文件类型'}, 400
                filepath = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])

            if edit_type == 'gemini':
                return self._edit_with_gemini(filepath, edit_params)
            elif edit_type == 'filter':
                return self._apply_filter(filepath, edit_params)
            elif edit_type == 'enhance':
                return self._enhance_image(filepath, edit_params)
            elif edit_type == 'transform':
                return self._transform_image(filepath, edit_params)
            elif edit_type == 'repair':
                return self._repair_image(filepath, edit_params)
            else:
                return {'success': False, 'error': '不支持的编辑类型'}, 400

        except Exception as e:
            error_msg = f'图像编辑失败: {str(e)}'
            print(f"图像编辑错误: {e}")
            return {'success': False, 'error': error_msg}, 500

    def _edit_with_gemini(self, filepath, edit_params):
        """使用 Gemini 进行 AI 图像编辑"""
        try:
            instruction = edit_params.get('instruction', '请编辑这张图像')
            gemini_model = edit_params.get('gemini_model', current_app.config['GEMINI_IMAGE_GEN_MODEL'])

            # 读取图像
            with open(filepath, 'rb') as f:
                image_bytes = f.read()

            # 使用指定的 Gemini 模型进行图像编辑
            response = self.client.models.generate_content(
                model=gemini_model,
                contents=[
                    instruction,
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
                ],
                config=types.GenerateContentConfig(response_modalities=["Text", "Image"])
            )

            # 处理响应
            edited_images = []
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    filename = f"gemini_edited_{hash(instruction) % 10000}_{os.path.basename(filepath)}"
                    output_path = os.path.join(current_app.config['GENERATED_FOLDER'], filename)

                    with open(output_path, 'wb') as f:
                        f.write(part.inline_data.data)

                    edited_images.append(output_path)

            if edited_images:
                # 转换为URL路径
                from ..utils.helpers import get_image_url
                edited_image_urls = [get_image_url(os.path.basename(path), 'generated') for path in edited_images]

                return {
                    'success': True,
                    'original_image': filepath,
                    'edited_images': edited_image_urls,
                    'edit_type': f'Gemini AI 编辑 ({gemini_model})',
                    'instruction': instruction
                }, 200
            else:
                return {'success': False, 'error': 'Gemini 未能生成编辑后的图像'}, 500

        except Exception as e:
            return {'success': False, 'error': f'Gemini 编辑失败: {str(e)}'}, 500

    def _apply_filter(self, filepath, edit_params):
        """应用图像滤镜"""
        filter_type = edit_params.get('filter_type', 'blur')
        intensity = edit_params.get('intensity', 1.0)

        # 使用 PIL 打开图像
        image = Image.open(filepath)

        edited_images = []

        if filter_type == 'blur':
            # 模糊滤镜
            filtered_image = image.filter(ImageFilter.GaussianBlur(radius=intensity))

        elif filter_type == 'sharpen':
            # 锐化滤镜
            filtered_image = image.filter(ImageFilter.SHARPEN)

        elif filter_type == 'edge':
            # 边缘检测
            filtered_image = image.filter(ImageFilter.FIND_EDGES)

        elif filter_type == 'emboss':
            # 浮雕效果
            filtered_image = image.filter(ImageFilter.EMBOSS)

        elif filter_type == 'vintage':
            # 复古效果
            filtered_image = ImageOps.colorize(
                ImageOps.grayscale(image),
                black="brown",
                white="wheat"
            )

        elif filter_type == 'sepia':
            # 棕褐色效果
            filtered_image = ImageOps.colorize(
                ImageOps.grayscale(image),
                black="black",
                white="#FFCC99"
            )

        else:
            return {'success': False, 'error': f'不支持的滤镜类型: {filter_type}'}, 400

        # 保存滤镜后的图像
        filename = f"filter_{filter_type}_{os.path.basename(filepath)}"
        output_path = os.path.join(current_app.config['GENERATED_FOLDER'], filename)
        filtered_image.save(output_path)
        edited_images.append(output_path)

        return {
            'success': True,
            'original_image': filepath,
            'edited_images': edited_images,
            'edit_type': f'{filter_type} 滤镜',
            'parameters': edit_params
        }, 200

    def _enhance_image(self, filepath, edit_params):
        """图像增强"""
        enhance_type = edit_params.get('enhance_type', 'brightness')
        factor = edit_params.get('factor', 1.2)

        image = Image.open(filepath)
        edited_images = []

        if enhance_type == 'brightness':
            # 亮度调整
            enhancer = ImageEnhance.Brightness(image)
            enhanced_image = enhancer.enhance(factor)

        elif enhance_type == 'contrast':
            # 对比度调整
            enhancer = ImageEnhance.Contrast(image)
            enhanced_image = enhancer.enhance(factor)

        elif enhance_type == 'color':
            # 色彩饱和度调整
            enhancer = ImageEnhance.Color(image)
            enhanced_image = enhancer.enhance(factor)

        elif enhance_type == 'sharpness':
            # 锐度调整
            enhancer = ImageEnhance.Sharpness(image)
            enhanced_image = enhancer.enhance(factor)

        elif enhance_type == 'auto':
            # 自动增强
            enhanced_image = ImageOps.autocontrast(image)
            enhanced_image = ImageOps.equalize(enhanced_image)

        else:
            return {'success': False, 'error': f'不支持的增强类型: {enhance_type}'}, 400

        # 保存增强后的图像
        filename = f"enhance_{enhance_type}_{os.path.basename(filepath)}"
        output_path = os.path.join(current_app.config['GENERATED_FOLDER'], filename)
        enhanced_image.save(output_path)
        edited_images.append(output_path)

        return {
            'success': True,
            'original_image': filepath,
            'edited_images': edited_images,
            'edit_type': f'{enhance_type} 增强',
            'parameters': edit_params
        }, 200

    def _transform_image(self, filepath, edit_params):
        """图像变换"""
        transform_type = edit_params.get('transform_type', 'resize')

        image = Image.open(filepath)
        edited_images = []

        if transform_type == 'resize':
            # 调整大小
            width = edit_params.get('width', 800)
            height = edit_params.get('height', 600)
            transformed_image = image.resize((width, height), Image.Resampling.LANCZOS)

        elif transform_type == 'rotate':
            # 旋转
            angle = edit_params.get('angle', 90)
            transformed_image = image.rotate(angle, expand=True)

        elif transform_type == 'flip_horizontal':
            # 水平翻转
            transformed_image = image.transpose(Image.FLIP_LEFT_RIGHT)

        elif transform_type == 'flip_vertical':
            # 垂直翻转
            transformed_image = image.transpose(Image.FLIP_TOP_BOTTOM)

        elif transform_type == 'crop':
            # 裁剪
            left = edit_params.get('left', 0)
            top = edit_params.get('top', 0)
            right = edit_params.get('right', image.width)
            bottom = edit_params.get('bottom', image.height)
            transformed_image = image.crop((left, top, right, bottom))

        elif transform_type == 'grayscale':
            # 转为灰度
            transformed_image = ImageOps.grayscale(image)

        else:
            return {'success': False, 'error': f'不支持的变换类型: {transform_type}'}, 400

        # 保存变换后的图像
        filename = f"transform_{transform_type}_{os.path.basename(filepath)}"
        output_path = os.path.join(current_app.config['GENERATED_FOLDER'], filename)
        transformed_image.save(output_path)
        edited_images.append(output_path)

        # 转换为URL路径
        from ..utils.helpers import get_image_url
        edited_image_urls = [get_image_url(os.path.basename(path), 'generated') for path in edited_images]

        return {
            'success': True,
            'original_image': filepath,
            'edited_images': edited_image_urls,
            'edit_type': f'{transform_type} 变换',
            'parameters': edit_params
        }, 200

    def _repair_image(self, filepath, edit_params):
        """图像修复"""
        repair_type = edit_params.get('repair_type', 'denoise')

        # 使用 OpenCV 读取图像
        image = cv2.imread(filepath)

        if repair_type == 'denoise':
            # 去噪
            repaired_image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

        elif repair_type == 'blur_removal':
            # 去模糊（锐化）
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            repaired_image = cv2.filter2D(image, -1, kernel)

        elif repair_type == 'histogram_eq':
            # 直方图均衡化
            yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            yuv[:,:,0] = cv2.equalizeHist(yuv[:,:,0])
            repaired_image = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

        elif repair_type == 'gamma_correction':
            # 伽马校正
            gamma = edit_params.get('gamma', 1.2)
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            repaired_image = cv2.LUT(image, table)

        else:
            return {'success': False, 'error': f'不支持的修复类型: {repair_type}'}, 400

        # 保存修复后的图像
        filename = f"repair_{repair_type}_{os.path.basename(filepath)}"
        output_path = os.path.join(current_app.config['GENERATED_FOLDER'], filename)
        cv2.imwrite(output_path, repaired_image)

        return {
            'success': True,
            'original_image': filepath,
            'edited_images': [output_path],
            'edit_type': f'{repair_type} 修复',
            'parameters': edit_params
        }, 200

    def get_available_operations(self):
        """获取可用的编辑操作"""
        return {
            'gemini': {
                'name': 'AI 智能编辑',
                'description': '使用 Gemini AI 进行智能图像编辑',
                'parameters': ['instruction']
            },
            'filter': {
                'name': '滤镜效果',
                'description': '应用各种图像滤镜',
                'types': ['blur', 'sharpen', 'edge', 'emboss', 'vintage', 'sepia'],
                'parameters': ['filter_type', 'intensity']
            },
            'enhance': {
                'name': '图像增强',
                'description': '调整图像的各种属性',
                'types': ['brightness', 'contrast', 'color', 'sharpness', 'auto'],
                'parameters': ['enhance_type', 'factor']
            },
            'transform': {
                'name': '图像变换',
                'description': '对图像进行几何变换',
                'types': ['resize', 'rotate', 'flip_horizontal', 'flip_vertical', 'crop', 'grayscale'],
                'parameters': ['transform_type', 'width', 'height', 'angle', 'left', 'top', 'right', 'bottom']
            },
            'repair': {
                'name': '图像修复',
                'description': '修复图像中的问题',
                'types': ['denoise', 'blur_removal', 'histogram_eq', 'gamma_correction'],
                'parameters': ['repair_type', 'gamma']
            }
        }
