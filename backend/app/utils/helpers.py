# -*- coding: utf-8 -*-
"""
工具函数模块
包含应用中使用的各种工具函数
"""

import os
import base64
import json
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import numpy as np
from google import genai
from google.genai import types
from flask import current_app, request


def allowed_file(filename):
    """检查文件扩展名是否被允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_uploaded_file(file, upload_folder):
    """保存上传的文件并返回路径"""
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    filename = file.filename
    filepath = os.path.join(upload_folder, filename)

    # 检查是否是SharedFileObject且文件已经存在于目标位置
    if hasattr(file, 'filepath') and os.path.exists(file.filepath):
        # 如果目标路径和源路径相同，直接返回源路径
        if os.path.abspath(file.filepath) == os.path.abspath(filepath):
            return file.filepath

    file.save(filepath)
    return filepath


def image_to_bytes(image_path):
    """将图像文件转换为字节"""
    with open(image_path, 'rb') as f:
        return f.read()


def bytes_to_image(image_bytes):
    """将字节转换为 PIL 图像"""
    return Image.open(BytesIO(image_bytes))


def save_generated_image(image_bytes, filename, generated_folder):
    """将生成的图像字节保存到文件"""
    if not os.path.exists(generated_folder):
        os.makedirs(generated_folder)

    filepath = os.path.join(generated_folder, filename)
    with open(filepath, 'wb') as f:
        f.write(image_bytes)

    # 在Docker环境中，同时保存到共享存储卷
    copy_to_shared_storage(filepath, filename)

    return filepath


def copy_to_shared_storage(source_path, filename):
    """将文件复制到共享存储卷（Docker环境）"""
    try:
        # 检查是否在Docker环境中
        shared_storage_path = '/storage/generated'
        if os.path.exists('/storage'):
            # 确保共享存储目录存在
            os.makedirs(shared_storage_path, exist_ok=True)

            # 复制文件到共享存储
            import shutil
            dest_path = os.path.join(shared_storage_path, filename)

            # 检查源文件和目标文件是否是同一个文件
            if os.path.abspath(source_path) != os.path.abspath(dest_path):
                shutil.copy2(source_path, dest_path)
                print(f"文件已复制到共享存储: {dest_path}")
            else:
                print(f"文件已在共享存储中: {dest_path}")
        else:
            print("非Docker环境，跳过共享存储复制")
    except Exception as e:
        # 在非Docker环境中，这个操作可能会失败，但不应该影响主要功能
        print(f"复制到共享存储失败: {str(e)}")
        pass


def get_image_url(filename, subfolder='generated'):
    """
    生成正确的图像URL，支持Docker和本地环境

    Args:
        filename: 图像文件名
        subfolder: 子文件夹名称 (generated, uploads等)

    Returns:
        str: 正确的图像URL路径
    """
    if not filename:
        return ''

    # 如果已经是完整的URL，直接返回
    if filename.startswith('http://') or filename.startswith('https://'):
        return filename

    # 如果已经是正确的相对路径格式，直接返回
    if filename.startswith(f'/storage/{subfolder}/'):
        return filename

    # 提取文件名（去除路径）
    if '/' in filename or '\\' in filename:
        filename = filename.split('/')[-1].split('\\')[-1]

    # 构建标准的URL路径
    return f"/storage/{subfolder}/{filename}"


def draw_bounding_box(image_path, bbox_coords, output_path, label=None):
    """在图像上绘制边界框"""
    image = Image.open(image_path)

    # 如果图像有透明通道，转换为RGB
    if image.mode in ('RGBA', 'LA', 'P'):
        # 创建白色背景
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    draw = ImageDraw.Draw(image)

    # 解析边界框坐标 [ymin, xmin, ymax, xmax]
    if len(bbox_coords) == 4:
        ymin, xmin, ymax, xmax = bbox_coords
        # 将归一化坐标转换为像素坐标
        width, height = image.size
        x1 = int(xmin * width)
        y1 = int(ymin * height)
        x2 = int(xmax * width)
        y2 = int(ymax * height)

        # 绘制红色矩形边界框
        draw.rectangle([x1, y1, x2, y2], outline="red", width=4)

        # 如果有标签，绘制标签文本
        if label:
            try:
                # 尝试加载字体
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
            except:
                font = ImageFont.load_default()

            # 绘制标签背景
            text_bbox = draw.textbbox((x1, y1-25), label, font=font)
            draw.rectangle(text_bbox, fill="red")
            # 绘制白色文本
            draw.text((x1, y1-25), label, fill="white", font=font)

    # 确保以JPEG格式保存
    if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
        image.save(output_path, 'JPEG', quality=95)
    else:
        image.save(output_path)

    # 复制到共享存储
    filename = os.path.basename(output_path)
    copy_to_shared_storage(output_path, filename)

    return output_path


def create_segmentation_overlay(original_image_path, mask_base64, output_path):
    """在原始图像上创建分割覆盖层"""
    # 加载原始图像
    original_image = Image.open(original_image_path).convert("RGBA")

    # 解码掩码
    if "base64," in mask_base64:
        mask_base64 = mask_base64.split("base64,")[1]

    mask_bytes = base64.b64decode(mask_base64)
    mask_image = Image.open(BytesIO(mask_bytes)).convert("L")

    # 创建彩色覆盖层
    overlay = Image.new("RGBA", mask_image.size, (255, 0, 255, 128))  # 粉色覆盖层
    overlay.putalpha(mask_image)

    # 如果需要，调整覆盖层大小以匹配原始图像
    if overlay.size != original_image.size:
        overlay = overlay.resize(original_image.size)

    # 合成图像
    result = Image.alpha_composite(original_image, overlay)
    result.save(output_path)
    return output_path


def create_segment_image(original_image_path, bbox_coords, output_path, label=None, expand_ratio=0.1):
    """根据边界框创建分割图像，支持边界框扩展以确保完整显示对象"""
    image = Image.open(original_image_path)

    # 如果图像有透明通道，转换为RGB
    if image.mode in ('RGBA', 'LA', 'P'):
        # 创建白色背景
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    # 解析边界框坐标 [ymin, xmin, ymax, xmax]
    if len(bbox_coords) == 4:
        ymin, xmin, ymax, xmax = bbox_coords
        # 将归一化坐标转换为像素坐标
        width, height = image.size

        # 计算原始边界框
        x1 = int(xmin * width)
        y1 = int(ymin * height)
        x2 = int(xmax * width)
        y2 = int(ymax * height)

        # 计算边界框的宽度和高度
        bbox_width = x2 - x1
        bbox_height = y2 - y1

        # 扩展边界框以确保完整显示对象
        expand_x = int(bbox_width * expand_ratio)
        expand_y = int(bbox_height * expand_ratio)

        # 应用扩展
        x1_expanded = max(0, x1 - expand_x)
        y1_expanded = max(0, y1 - expand_y)
        x2_expanded = min(width, x2 + expand_x)
        y2_expanded = min(height, y2 + expand_y)

        # 确保扩展后的坐标有效
        if x2_expanded <= x1_expanded:
            x2_expanded = min(width, x1_expanded + 50)
        if y2_expanded <= y1_expanded:
            y2_expanded = min(height, y1_expanded + 50)

        # 裁剪图像
        cropped_image = image.crop((x1_expanded, y1_expanded, x2_expanded, y2_expanded))

        # 如果裁剪的图像太小，调整大小但保持宽高比
        min_size = 100
        if cropped_image.size[0] < min_size or cropped_image.size[1] < min_size:
            # 计算缩放比例
            scale_x = min_size / cropped_image.size[0] if cropped_image.size[0] < min_size else 1
            scale_y = min_size / cropped_image.size[1] if cropped_image.size[1] < min_size else 1
            scale = max(scale_x, scale_y)

            new_width = int(cropped_image.size[0] * scale)
            new_height = int(cropped_image.size[1] * scale)
            cropped_image = cropped_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 确保以JPEG格式保存
        if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
            cropped_image.save(output_path, 'JPEG', quality=95)
        else:
            cropped_image.save(output_path)
        return output_path

    return None


def translate_chinese_to_english(chinese_text, client):
    """将中文文本翻译为英文，用于图像生成"""
    try:
        prompt = f"""
        请将以下中文文本翻译为英文，用于AI图像生成。
        翻译要求：
        1. 保持原意准确
        2. 使用适合图像生成的描述性语言
        3. 只返回英文翻译结果，不要其他内容

        中文文本：{chinese_text}
        """

        response = client.models.generate_content(
            model=current_app.config['DEFAULT_VISION_MODEL'],
            contents=[types.Part.from_text(text=prompt)]
        )

        english_text = response.text.strip()
        # 移除可能的引号或其他标点
        english_text = english_text.strip('"\'')
        return english_text

    except Exception as e:
        print(f"翻译失败: {e}")
        # 如果翻译失败，返回原文
        return chinese_text


def init_gemini_client():
    """初始化 Gemini 客户端"""
    # 首先尝试从环境变量获取API密钥
    api_key = current_app.config.get('GOOGLE_API_KEY')

    if not api_key:
        api_key = current_app.config.get('GEMINI_API_KEY')

    # 如果环境变量中没有API密钥，则从请求头中获取用户提供的密钥
    if not api_key:
        api_key = request.headers.get('X-API-Key')
    print("API_KEY",api_key)
    if not api_key:
        raise ValueError("未找到有效的API密钥，请在环境变量中设置GEMINI_API_KEY或在请求头中提供X-API-Key")

    return genai.Client(api_key=api_key)


def handle_api_error(error, operation_name="操作"):
    """
    统一处理API错误，返回友好的错误消息和适当的状态码

    Args:
        error: 异常对象
        operation_name: 操作名称，用于错误消息

    Returns:
        tuple: (error_response_dict, status_code)
    """
    error_str = str(error)
    print(f"{operation_name}错误: {error}")

    # API密钥相关错误
    if ('API key not valid' in error_str or
        'INVALID_ARGUMENT' in error_str or
        'API_KEY_INVALID' in error_str or
        '400' in error_str and 'key' in error_str.lower()):
        return {
            'success': False,
            'error': 'API密钥无效或已过期，请检查您的Google API密钥配置',
            'error_type': 'api_key_invalid',
            'suggestion': '请确认API密钥是否正确，或尝试重新生成API密钥'
        }, 400

    # 认证错误
    elif ('401' in error_str or
          'UNAUTHENTICATED' in error_str or
          'authentication' in error_str.lower()):
        return {
            'success': False,
            'error': 'API认证失败，请检查您的API密钥',
            'error_type': 'authentication_failed',
            'suggestion': '请确认API密钥是否有效，或联系管理员'
        }, 400

    # 配额限制错误
    elif ('429' in error_str or
          'RESOURCE_EXHAUSTED' in error_str or
          'quota' in error_str.lower() or
          'rate limit' in error_str.lower()):
        return {
            'success': False,
            'error': 'API调用次数已达到限制，请稍后再试',
            'error_type': 'quota_exceeded',
            'suggestion': '请等待一段时间后重试，或检查API配额设置'
        }, 400

    # 网络连接错误
    elif ('connection' in error_str.lower() or
          'network' in error_str.lower() or
          'timeout' in error_str.lower() or
          'ConnectTimeout' in error_str):
        return {
            'success': False,
            'error': '网络连接失败，请检查网络连接后重试',
            'error_type': 'network_error',
            'suggestion': '请检查网络连接，或稍后重试'
        }, 400

    # 服务不可用错误
    elif ('503' in error_str or
          'SERVICE_UNAVAILABLE' in error_str or
          'service unavailable' in error_str.lower()):
        return {
            'success': False,
            'error': '服务暂时不可用，请稍后重试',
            'error_type': 'service_unavailable',
            'suggestion': '服务可能正在维护，请稍后重试'
        }, 400

    # 内容安全策略错误
    elif ('SAFETY' in error_str or
          'safety' in error_str.lower() or
          'content policy' in error_str.lower()):
        return {
            'success': False,
            'error': '内容不符合安全策略，请修改后重试',
            'error_type': 'content_policy_violation',
            'suggestion': '请检查输入内容是否包含不当信息，并进行修改'
        }, 400

    # 其他未知错误 - 返回友好的通用错误消息
    else:
        return {
            'success': False,
            'error': f'{operation_name}暂时失败，请稍后重试',
            'error_type': 'unknown_error',
            'suggestion': '如果问题持续存在，请联系技术支持',
            'technical_details': error_str if current_app.debug else None
        }, 400


def draw_all_bounding_boxes(image_path, detected_objects, output_path):
    """在一张图像上绘制所有检测到的对象的边界框"""
    image = Image.open(image_path)

    # 如果图像有透明通道，转换为RGB
    if image.mode in ('RGBA', 'LA', 'P'):
        # 创建白色背景
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    draw = ImageDraw.Draw(image)
    width, height = image.size

    # 为不同的对象使用不同的颜色
    colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'cyan', 'magenta']

    for i, obj in enumerate(detected_objects):
        bbox = obj.get('bbox', [])
        label = obj.get('label', '对象')
        confidence = obj.get('confidence', 0.9)

        if len(bbox) == 4:
            ymin, xmin, ymax, xmax = bbox
            # 将归一化坐标转换为像素坐标
            x1 = int(xmin * width)
            y1 = int(ymin * height)
            x2 = int(xmax * width)
            y2 = int(ymax * height)

            # 选择颜色
            color = colors[i % len(colors)]

            # 绘制边界框
            draw.rectangle([x1, y1, x2, y2], outline=color, width=4)

            # 绘制标签
            try:
                # 尝试加载字体
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
            except:
                font = ImageFont.load_default()

            # 创建标签文本
            label_text = f"{label} ({confidence:.2f})"

            # 绘制标签背景
            text_bbox = draw.textbbox((x1, y1-25), label_text, font=font)
            draw.rectangle(text_bbox, fill=color)
            # 绘制白色文本
            draw.text((x1, y1-25), label_text, fill="white", font=font)

    # 保存图像
    if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
        image.save(output_path, 'JPEG', quality=95)
    else:
        image.save(output_path)

    # 复制到共享存储
    filename = os.path.basename(output_path)
    copy_to_shared_storage(output_path, filename)

    return output_path
