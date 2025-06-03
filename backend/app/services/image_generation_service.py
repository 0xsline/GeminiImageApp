"""
图像生成服务
"""
import os
import time
import base64
from google import genai
from google.genai import types
from ..utils.helpers import save_generated_image
from flask import current_app


class ImageGenerationService:
    def __init__(self, client=None):
        """初始化图像生成服务"""
        if client is None:
            # 如果没有提供client，创建一个新的
            self.client = genai.Client(api_key=current_app.config['GEMINI_API_KEY'])
        else:
            self.client = client

    def optimize_prompt(self, user_prompt, style="realistic"):
        """
        使用 Gemini 优化用户的图像生成提示词
        """
        try:
            optimization_prompt = f"""
请优化以下图像生成提示词，使其更适合Imagen 3.0图像生成模型。
优化要求：
1. 添加具体的视觉细节描述
2. 包含艺术风格和技术参数
3. 指定光照、构图和色彩
4. 添加质量和分辨率要求
5. 确保描述清晰、具体且富有创意
6. 保持原始意图不变
7. 使用英文，因为英文效果更好

风格要求：{style}
原始提示词：{user_prompt}

请返回优化后的英文提示词：
"""

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=optimization_prompt
            )

            optimized_prompt = response.text.strip()

            # 如果返回的内容包含引号或其他格式，清理一下
            if optimized_prompt.startswith('"') and optimized_prompt.endswith('"'):
                optimized_prompt = optimized_prompt[1:-1]

            return {
                'original_prompt': user_prompt,
                'optimized_prompt': optimized_prompt
            }

        except Exception as e:
            print(f"提示词优化失败: {str(e)}")
            # 如果优化失败，返回原始提示词
            return {
                'original_prompt': user_prompt,
                'optimized_prompt': user_prompt
            }

    def generate_image(self, prompt, model_type='imagen-3.0-generate-002', aspect_ratio='1:1', style='realistic', num_images=1):
        """
        生成图像 - 支持多种模型动态选择
        """
        try:
            # 获取模型信息
            model_options = self.get_model_options()

            # 处理旧的模型类型兼容性
            if model_type == 'imagen-3':
                model_type = 'imagen-3.0-generate-002'  # 默认使用最新版本

            # 验证模型是否存在
            if model_type not in model_options:
                model_type = 'imagen-3.0-generate-002'  # 回退到默认模型

            model_info = model_options[model_type]
            actual_model_id = model_info['model_id']
            model_name = model_info['name']

            print(f"正在调用 {model_name} 图像生成API...")
            print(f"模型ID: {actual_model_id}")

            # 验证宽高比是否支持
            validated_aspect_ratio = self._validate_aspect_ratio(aspect_ratio, model_info['type'])
            if validated_aspect_ratio != aspect_ratio:
                print(f"宽高比 {aspect_ratio} 不支持，已调整为 {validated_aspect_ratio}")
                aspect_ratio = validated_aspect_ratio

            # 首先优化提示词
            prompt_optimization = self.optimize_prompt(prompt, style)
            optimized_prompt = prompt_optimization['optimized_prompt']
            print(f"优化后的提示词: {optimized_prompt}")

            # 根据模型类型选择不同的API调用方式
            if model_info['type'] == 'gemini':
                # 使用 Gemini 2.0 Flash 图像生成
                return self._generate_with_gemini(actual_model_id, optimized_prompt, aspect_ratio, style, num_images, model_name, prompt)
            else:
                # 使用 Imagen 系列模型
                return self._generate_with_imagen(actual_model_id, optimized_prompt, aspect_ratio, style, num_images, model_name, prompt)

        except Exception as e:
            error_msg = f"图像生成失败: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg
            }, 500

    def _generate_with_imagen(self, model_id, optimized_prompt, aspect_ratio, style, num_images, model_name, original_prompt):
        """使用 Imagen 系列模型生成图像"""
        try:
            response = self.client.models.generate_images(
                model=model_id,
                prompt=optimized_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=num_images,
                    aspect_ratio=aspect_ratio,
                    safety_filter_level="BLOCK_LOW_AND_ABOVE",
                    person_generation="allow_adult",
                ),
            )

            if response.generated_images and len(response.generated_images) > 0:
                generated_images = []

                for i, generated_image in enumerate(response.generated_images):
                    # 保存图像
                    timestamp = int(time.time())
                    image_filename = f"imagen_generated_{timestamp}_{i}.png"

                    image_path = save_generated_image(
                        generated_image.image.image_bytes,
                        image_filename,
                        current_app.config['GENERATED_FOLDER']
                    )

                    # 使用统一的URL生成函数
                    from ..utils.helpers import get_image_url
                    image_url = get_image_url(image_filename, 'generated')
                    generated_images.append({
                        'path': image_url,
                        'filename': image_filename
                    })

                return {
                    'success': True,
                    'status': 'image_generated',
                    'message': '图像生成成功！',
                    'images': generated_images,
                    'image_path': generated_images[0]['path'] if generated_images else None,
                    'original_prompt': original_prompt,
                    'optimized_prompt': optimized_prompt,
                    'model': model_name,
                    'model_id': model_id,
                    'aspect_ratio': aspect_ratio,
                    'style': style,
                    'num_images': len(generated_images),
                    'note': f'{model_name} 图像生成完成'
                }, 200

            else:
                raise Exception("未生成任何图像")

        except Exception as imagen_api_error:
            error_str = str(imagen_api_error)
            print(f"{model_name} API调用失败: {error_str}")

            # 检查是否是API密钥相关错误
            if ('API key not valid' in error_str or
                'INVALID_ARGUMENT' in error_str or
                '400' in error_str or
                'API_KEY_INVALID' in error_str):
                return {
                    'success': False,
                    'error': 'API密钥无效或已过期，请检查您的Google API密钥配置',
                    'error_type': 'api_key_invalid'
                }, 400

            # 检查是否是认证错误
            elif ('401' in error_str or
                  'UNAUTHENTICATED' in error_str):
                return {
                    'success': False,
                    'error': 'API认证失败，请检查您的API密钥',
                    'error_type': 'authentication_failed'
                }, 401

            # 检查是否是配额限制错误
            elif ('429' in error_str or
                  'RESOURCE_EXHAUSTED' in error_str or
                  'quota' in error_str.lower()):
                return {
                    'success': False,
                    'error': 'API调用次数已达到限制，请稍后再试',
                    'error_type': 'quota_exceeded'
                }, 429

            # 其他情况，生成详细的创作方案作为备选
            else:
                return self._generate_image_creation_plan(optimized_prompt, aspect_ratio, style)

    def _generate_with_gemini(self, model_id, optimized_prompt, aspect_ratio, style, num_images, model_name, original_prompt):
        """使用 Gemini 2.0 Flash 图像生成"""
        try:
            # Gemini 2.0 Flash 使用不同的API调用方式
            response = self.client.models.generate_content(
                model=model_id,
                contents=optimized_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["Text", "Image"],
                    # Gemini 2.0 Flash 的特定配置
                )
            )

            # 处理 Gemini 2.0 Flash 的响应
            if hasattr(response, 'candidates') and response.candidates:
                generated_images = []

                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                # 保存图像
                                timestamp = int(time.time())
                                image_filename = f"gemini_generated_{timestamp}.png"

                                # 处理 Gemini 的图像数据
                                image_data = part.inline_data.data
                                if isinstance(image_data, str):
                                    # 如果是base64编码的字符串
                                    import base64
                                    image_bytes = base64.b64decode(image_data)
                                else:
                                    image_bytes = image_data

                                image_path = save_generated_image(
                                    image_bytes,
                                    image_filename,
                                    current_app.config['GENERATED_FOLDER']
                                )

                                # 使用统一的URL生成函数
                                from ..utils.helpers import get_image_url
                                image_url = get_image_url(image_filename, 'generated')
                                generated_images.append({
                                    'path': image_url,
                                    'filename': image_filename
                                })

                if generated_images:
                    return {
                        'success': True,
                        'status': 'image_generated',
                        'message': '图像生成成功！',
                        'images': generated_images,
                        'image_path': generated_images[0]['path'] if generated_images else None,
                        'original_prompt': original_prompt,
                        'optimized_prompt': optimized_prompt,
                        'model': model_name,
                        'model_id': model_id,
                        'aspect_ratio': aspect_ratio,
                        'style': style,
                        'num_images': len(generated_images),
                        'note': f'{model_name} 对话式图像生成完成',
                        'response_text': response.text if hasattr(response, 'text') else None
                    }, 200
                else:
                    raise Exception("未生成任何图像")
            else:
                raise Exception("Gemini响应格式异常")

        except Exception as gemini_api_error:
            error_str = str(gemini_api_error)
            print(f"{model_name} API调用失败: {error_str}")

            # 检查是否是API密钥相关错误
            if ('API key not valid' in error_str or
                'INVALID_ARGUMENT' in error_str or
                '400' in error_str or
                'API_KEY_INVALID' in error_str):
                return {
                    'success': False,
                    'error': 'API密钥无效或已过期，请检查您的Google API密钥配置',
                    'error_type': 'api_key_invalid'
                }, 400

            # 检查是否是认证错误
            elif ('401' in error_str or
                  'UNAUTHENTICATED' in error_str):
                return {
                    'success': False,
                    'error': 'API认证失败，请检查您的API密钥',
                    'error_type': 'authentication_failed'
                }, 401

            # 检查是否是配额限制错误
            elif ('429' in error_str or
                  'RESOURCE_EXHAUSTED' in error_str or
                  'quota' in error_str.lower()):
                return {
                    'success': False,
                    'error': 'API调用次数已达到限制，请稍后再试',
                    'error_type': 'quota_exceeded'
                }, 429

            # 其他情况，生成详细的创作方案作为备选
            else:
                return self._generate_image_creation_plan(optimized_prompt, aspect_ratio, style)

    def edit_image(self, image_path, edit_prompt, mask_path=None, model_type='imagen-3.0-generate-002'):
        """
        编辑图像 - 支持多种 Imagen 模型的图像编辑功能
        """
        try:
            # 获取模型信息
            model_options = self.get_model_options()

            # 处理旧的模型类型兼容性
            if model_type == 'imagen-3':
                model_type = 'imagen-3.0-generate-002'

            # 验证模型是否存在且支持编辑
            if model_type not in model_options or model_options[model_type]['type'] != 'imagen':
                model_type = 'imagen-3.0-generate-002'  # 回退到默认Imagen模型

            model_info = model_options[model_type]
            actual_model_id = model_info['model_id']
            model_name = model_info['name']

            print(f"正在使用 {model_name} 编辑图像...")
            print(f"模型ID: {actual_model_id}")

            # 优化编辑提示词
            prompt_optimization = self.optimize_prompt(edit_prompt, "realistic")
            optimized_prompt = prompt_optimization['optimized_prompt']
            print(f"编辑提示词: {optimized_prompt}")

            # 读取原始图像
            from PIL import Image
            base_image = Image.open(image_path)

            # 如果有遮罩，读取遮罩图像
            mask_image = None
            if mask_path and os.path.exists(mask_path):
                mask_image = Image.open(mask_path)

            try:
                # 准备参考图像
                reference_images = [
                    types.RawReferenceImage(
                        reference_id=1,
                        reference_image=base_image
                    )
                ]

                # 如果有遮罩图像，添加遮罩参考
                if mask_image:
                    reference_images.append(
                        types.MaskReferenceImage(
                            reference_id=2,
                            reference_image=mask_image,
                            config=types.MaskReferenceConfig(
                                mask_mode="MASK_MODE_FOREGROUND",
                                mask_dilation=0.0,
                            )
                        )
                    )

                # 使用新的图像编辑API
                response = self.client.models.edit_image(
                    model=actual_model_id,
                    prompt=optimized_prompt,
                    reference_images=reference_images,
                    config=types.EditImageConfig(
                        number_of_images=1,
                        safety_filter_level="BLOCK_LOW_AND_ABOVE",
                        edit_mode="EDIT_MODE_INPAINT_INSERTION" if mask_image else "EDIT_MODE_DEFAULT",
                    ),
                )

                if response.generated_images and len(response.generated_images) > 0:
                    # 保存编辑后的图像
                    timestamp = int(time.time())
                    edited_filename = f"imagen3_edited_{timestamp}.png"

                    edited_path = save_generated_image(
                        response.generated_images[0].image.image_bytes,
                        edited_filename,
                        current_app.config['GENERATED_FOLDER']
                    )

                    # 使用统一的URL生成函数
                    from ..utils.helpers import get_image_url
                    edited_image_url = get_image_url(edited_filename, 'generated')
                    return {
                        'success': True,
                        'status': 'image_edited',
                        'message': '图像编辑成功！',
                        'edited_image_path': edited_image_url,
                        'original_image_path': image_path,
                        'edit_prompt': edit_prompt,
                        'optimized_prompt': optimized_prompt,
                        'model': 'Imagen 3.0 Edit',
                        'note': 'Imagen 3.0 图像编辑完成'
                    }, 200

                else:
                    raise Exception("图像编辑失败，未生成结果")

            except Exception as edit_api_error:
                print(f"Imagen 3.0 编辑API调用失败: {str(edit_api_error)}")
                return {
                    'success': False,
                    'error': f'图像编辑API调用失败: {str(edit_api_error)}'
                }, 500

        except Exception as e:
            error_msg = f"图像编辑失败: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg
            }, 500

    def get_image_styles(self):
        """获取可用的图像风格选项"""
        return {
            'realistic': {
                'name': '写实风格',
                'description': '真实感强的图像风格，适合人像和风景',
                'keywords': 'photorealistic, natural lighting, high detail, professional photography'
            },
            'artistic': {
                'name': '艺术风格',
                'description': '艺术化的创意风格，独特的美学表现',
                'keywords': 'artistic, creative, stylized, unique aesthetic, fine art'
            },
            'cartoon': {
                'name': '卡通风格',
                'description': '卡通动画风格，适合可爱和创意内容',
                'keywords': 'cartoon style, animated, colorful, cute, illustration'
            },
            'vintage': {
                'name': '复古风格',
                'description': '怀旧复古的视觉风格',
                'keywords': 'vintage, retro, classic, nostalgic, film grain, sepia'
            },
            'futuristic': {
                'name': '未来风格',
                'description': '科幻未来感的视觉效果',
                'keywords': 'futuristic, sci-fi, cyberpunk, neon, high-tech, digital art'
            },
            'minimalist': {
                'name': '极简风格',
                'description': '简洁明了的设计风格',
                'keywords': 'minimalist, clean, simple, modern, geometric'
            },
            'fantasy': {
                'name': '奇幻风格',
                'description': '奇幻魔法风格，超现实的视觉效果',
                'keywords': 'fantasy, magical, surreal, mystical, ethereal'
            },
            'abstract': {
                'name': '抽象风格',
                'description': '抽象艺术风格，非具象表现',
                'keywords': 'abstract, non-representational, geometric, expressionist'
            }
        }

    def get_aspect_ratio_options(self):
        """获取可用的宽高比选项 - 基于Imagen 3官方支持的比例"""
        return {
            "1:1": {
                'name': '正方形 (1:1)',
                'description': '适合社交媒体头像、图标',
                'use_case': 'Instagram帖子、头像、图标',
                'supported_models': ['imagen', 'gemini']
            },
            "4:3": {
                'name': '标准 (4:3)',
                'description': '传统照片比例，适合打印',
                'use_case': '传统照片、打印、展示',
                'supported_models': ['imagen', 'gemini']
            },
            "3:4": {
                'name': '竖版标准 (3:4)',
                'description': '竖版传统照片比例',
                'use_case': '竖版照片、人像摄影、海报',
                'supported_models': ['imagen', 'gemini']
            },
            "16:9": {
                'name': '宽屏 (16:9)',
                'description': '适合横屏显示、背景图',
                'use_case': '电脑壁纸、横屏展示、视频缩略图',
                'supported_models': ['imagen', 'gemini']
            },
            "9:16": {
                'name': '竖屏 (9:16)',
                'description': '适合手机屏幕、竖屏内容',
                'use_case': '手机壁纸、Stories、竖屏海报',
                'supported_models': ['imagen', 'gemini']
            }
        }

    def _validate_aspect_ratio(self, aspect_ratio, model_type):
        """验证并修正宽高比，确保与模型兼容"""
        supported_ratios = self.get_aspect_ratio_options()

        # 检查宽高比是否在支持列表中
        if aspect_ratio in supported_ratios:
            # 检查该宽高比是否支持当前模型类型
            if model_type in supported_ratios[aspect_ratio]['supported_models']:
                return aspect_ratio

        # 如果不支持，返回默认的1:1比例
        print(f"宽高比 {aspect_ratio} 不支持 {model_type} 模型，使用默认比例 1:1")
        return "1:1"

    def get_model_options(self):
        """获取可用的模型选项 - 基于Google AI官方文档最新模型（2025年5月24日）"""
        return {
            'imagen-3.0-generate-002': {
                'name': 'Imagen 3 (官方最新)',
                'description': 'Google最高质量的文本到图像模型，具有新的和改进的功能',
                'features': ['最高质量生成', '更好的细节', '更丰富的光照', '更少的干扰伪影', '支持人物生成'],
                'model_id': 'imagen-3.0-generate-002',
                'type': 'imagen',
                'release_date': '2025年2月',
                'pricing': '按图像计费',
                'official': True,
                'recommended': True
            },
            'gemini-2.0-flash-preview-image-generation': {
                'name': 'Gemini 2.0 Flash 图像生成 (预览)',
                'description': 'Gemini 2.0 Flash的图像生成功能，支持对话式图像生成和编辑',
                'features': ['对话式生成', '图像生成和编辑', '文本+图像输出', '支持音频/视频/文本输入'],
                'model_id': 'gemini-2.0-flash-preview-image-generation',
                'type': 'gemini',
                'release_date': '2025年5月',
                'pricing': '预览版定价',
                'official': True,
                'experimental': True,
                'input_token_limit': 32000,
                'output_token_limit': 8192
            }
        }

    def _generate_image_creation_plan(self, prompt, aspect_ratio, style):
        """
        生成图像创作方案（当API不可用时的备选方案）
        """
        try:
            plan_prompt = f"""
作为专业的图像设计师，请为以下图像需求制定详细的创作方案：

图像描述：{prompt}
宽高比：{aspect_ratio}
风格：{style}

请提供以下内容：
1. 构图建议（主体位置、背景安排、视觉焦点）
2. 色彩方案（主色调、配色建议、色彩心理学）
3. 光影设计（光源方向、阴影处理、氛围营造）
4. 细节描述（纹理、材质、装饰元素）
5. 技术参数（分辨率、格式、后期处理）
6. 创作工具推荐（软件、插件、资源）
7. 参考作品建议
8. 创作步骤指导

请以专业且实用的方式组织这些信息。
"""

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=plan_prompt
            )

            plan_content = response.text

            return {
                'success': True,
                'status': 'plan_generated',
                'message': 'Imagen 3.0暂时不可用，已生成详细的图像创作方案',
                'creation_plan': plan_content,
                'original_prompt': prompt,
                'aspect_ratio': aspect_ratio,
                'style': style,
                'note': '这是一个详细的创作方案，您可以使用专业图像设计软件来实现'
            }, 200

        except Exception as e:
            print(f"生成创作方案失败: {str(e)}")
            return {
                'success': False,
                'error': f'无法生成图像创作方案: {str(e)}'
            }, 500

    def upscale_image(self, image_path, scale_factor=2):
        """
        图像放大功能（如果API支持）
        """
        try:
            # 这里可以添加图像放大的逻辑
            # 目前Imagen 3.0可能不直接支持放大，可以使用其他方法

            from PIL import Image
            import numpy as np

            # 简单的双线性插值放大
            original_image = Image.open(image_path)
            width, height = original_image.size
            new_size = (width * scale_factor, height * scale_factor)

            upscaled_image = original_image.resize(new_size, Image.Resampling.LANCZOS)

            # 保存放大后的图像
            timestamp = int(time.time())
            upscaled_filename = f"upscaled_{scale_factor}x_{timestamp}.png"
            upscaled_path = os.path.join(current_app.config['GENERATED_FOLDER'], upscaled_filename)

            upscaled_image.save(upscaled_path)

            return {
                'success': True,
                'status': 'image_upscaled',
                'message': f'图像已放大{scale_factor}倍',
                'upscaled_image_path': upscaled_path,
                'original_image_path': image_path,
                'scale_factor': scale_factor,
                'original_size': f"{width}x{height}",
                'new_size': f"{new_size[0]}x{new_size[1]}",
                'note': '使用高质量插值算法放大'
            }, 200

        except Exception as e:
            error_msg = f"图像放大失败: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg
            }, 500

    def generate_variations(self, image_path, num_variations=3):
        """
        生成图像变体
        """
        try:
            # 分析原始图像并生成变体提示词
            analysis_prompt = f"""
请分析这张图像的主要特征，并为生成{num_variations}个变体提供不同的提示词。
每个变体应该保持原始图像的核心元素，但在风格、色彩、构图或细节上有所不同。

请为每个变体提供一个详细的英文提示词。
"""

            # 这里可以添加图像分析和变体生成的逻辑
            # 目前先返回一个基本的响应

            return {
                'success': True,
                'status': 'variations_planned',
                'message': f'已规划{num_variations}个图像变体',
                'original_image_path': image_path,
                'num_variations': num_variations,
                'note': '变体生成功能正在开发中'
            }, 200

        except Exception as e:
            error_msg = f"生成图像变体失败: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg
            }, 500
