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
from flask import current_app


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
    return filepath


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
    return genai.Client(api_key=current_app.config['GOOGLE_API_KEY'])


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
    return output_path
