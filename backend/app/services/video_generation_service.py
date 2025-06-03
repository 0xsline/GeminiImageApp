"""
视频生成服务
使用 Veo 2.0 模型生成视频内容
"""
import os
import time
from google import genai
from google.genai import types
from ..utils.helpers import save_generated_image
from flask import current_app


class VideoGenerationService:
    def __init__(self, client=None):
        """初始化视频生成服务"""
        if client is None:
            # 如果没有提供client，创建一个新的
            self.client = genai.Client(api_key=current_app.config['GEMINI_API_KEY'])
        else:
            self.client = client

    def optimize_prompt(self, user_prompt):
        """
        使用 Gemini 优化用户的视频生成提示词
        """
        try:
            optimization_prompt = f"""
请优化以下视频生成提示词，使其更适合Veo 2.0视频生成模型。
优化要求：
1. 添加具体的视觉细节描述
2. 包含摄像机角度和运动描述（如：dolly shot, tracking shot, aerial view等）
3. 指定画面风格和色调
4. 添加时长和节奏建议
5. 确保描述清晰、具体且富有创意
6. 保持原始意图不变
7. 使用英文，因为Veo 2.0对英文效果更好

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

    def generate_video(self, prompt, duration=8, style="realistic", aspect_ratio="16:9"):
        """
        生成视频 - 使用 Veo 2.0 视频生成模型
        """
        try:
            # 首先优化提示词
            prompt_optimization = self.optimize_prompt(prompt)
            optimized_prompt = prompt_optimization['optimized_prompt']

            print(f"正在调用Veo 2.0视频生成API...")
            print(f"优化后的提示词: {optimized_prompt}")

            # 使用最新的Veo 2.0 API调用方式
            try:
                # 根据2025年最新官方文档使用正确的API调用方式
                operation = self.client.models.generate_videos(
                    model="veo-2.0-generate-001",
                    prompt=optimized_prompt,
                    config=types.GenerateVideosConfig(
                        person_generation="dont_allow",  # 安全设置
                        aspect_ratio=aspect_ratio,  # "16:9" 或 "9:16"
                        duration_seconds=min(duration, 8),  # 最大8秒
                        number_of_videos=1,
                        enhance_prompt=True,  # 启用提示词增强
                    ),
                )

                print(f"视频生成操作已启动: {operation.name}")

                # 轮询操作状态
                max_wait_time = 600  # 最大等待10分钟
                wait_time = 0
                poll_interval = 20  # 每20秒检查一次

                while not operation.done and wait_time < max_wait_time:
                    print(f"等待视频生成中... ({wait_time}/{max_wait_time}秒)")
                    time.sleep(poll_interval)
                    wait_time += poll_interval
                    operation = self.client.operations.get(operation)

                # 检查生成结果
                if operation.done:
                    if hasattr(operation, 'response') and operation.response:
                        generated_videos = operation.response.generated_videos
                        if generated_videos and len(generated_videos) > 0:
                            # 获取第一个生成的视频
                            video = generated_videos[0].video

                            # 下载视频文件
                            timestamp = int(time.time())
                            video_filename = f"veo2_generated_video_{timestamp}.mp4"
                            video_filepath = os.path.join(current_app.config['GENERATED_FOLDER'], video_filename)

                            try:
                                # 根据2025年最新API文档下载和保存视频
                                # 获取视频的URI或直接保存
                                if hasattr(video, 'uri'):
                                    # 如果有URI，下载视频内容
                                    video_data = self.client.files.download(video.uri)
                                    with open(video_filepath, 'wb') as f:
                                        f.write(video_data)
                                elif hasattr(video, 'save'):
                                    # 如果有save方法，直接保存
                                    video.save(video_filepath)
                                else:
                                    # 其他情况，尝试获取视频数据
                                    print(f"视频对象类型: {type(video)}")
                                    print(f"视频对象属性: {dir(video)}")
                                    raise Exception("无法确定视频保存方法")

                                # 生成预览图
                                preview_image_path = self._generate_preview_image(prompt, style)

                                return {
                                    'success': True,
                                    'status': 'video_generated',
                                    'message': '视频生成成功！',
                                    'video_path': video_filepath,
                                    'video_filename': video_filename,
                                    'preview_image': preview_image_path,
                                    'original_prompt': prompt,
                                    'optimized_prompt': optimized_prompt,
                                    'duration': duration,
                                    'style': style,
                                    'aspect_ratio': aspect_ratio,
                                    'model': 'Veo 2.0',
                                    'note': 'Veo 2.0 视频生成完成'
                                }, 200

                            except Exception as download_error:
                                print(f"视频保存失败: {str(download_error)}")
                                # 即使保存失败，也返回成功状态和视频信息
                                return {
                                    'success': True,
                                    'status': 'video_generated',
                                    'message': '视频生成成功，但本地保存失败',
                                    'video_info': {
                                        'type': str(type(video)),
                                        'attributes': [attr for attr in dir(video) if not attr.startswith('_')],
                                        'uri': getattr(video, 'uri', 'N/A'),
                                        'name': getattr(video, 'name', 'N/A')
                                    },
                                    'original_prompt': prompt,
                                    'optimized_prompt': optimized_prompt,
                                    'duration': duration,
                                    'style': style,
                                    'aspect_ratio': aspect_ratio,
                                    'model': 'Veo 2.0',
                                    'note': f'视频已生成但保存失败: {str(download_error)}'
                                }, 200
                        else:
                            raise Exception("未找到生成的视频")
                    else:
                        raise Exception("操作完成但无结果数据")
                else:
                    # 超时情况
                    print("视频生成超时，生成详细制作方案")
                    return self._generate_enhanced_video_plan(optimized_prompt, duration, style, aspect_ratio)

            except Exception as video_api_error:
                print(f"Veo 2.0 API调用失败: {str(video_api_error)}")
                # 如果Veo 2.0不可用，生成详细的制作方案
                return self._generate_enhanced_video_plan(optimized_prompt, duration, style, aspect_ratio)

        except Exception as e:
            error_msg = f"视频生成失败: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg
            }, 500

    def generate_video_from_image(self, image_path, prompt="", duration=8, aspect_ratio="16:9"):
        """
        从图像生成视频 - 图像到视频功能
        """
        try:
            # 优化提示词
            if prompt:
                prompt_optimization = self.optimize_prompt(prompt)
                optimized_prompt = prompt_optimization['optimized_prompt']
            else:
                optimized_prompt = "Animate this image with natural motion and cinematic quality"

            print(f"正在从图像生成视频...")
            print(f"提示词: {optimized_prompt}")

            # 读取图像
            from PIL import Image
            image = Image.open(image_path)

            # 使用图像到视频API
            operation = self.client.models.generate_videos(
                model="veo-2.0-generate-001",
                prompt=optimized_prompt,
                image=image,
                config=types.GenerateVideosConfig(
                    person_generation="dont_allow",
                    aspect_ratio=aspect_ratio,
                    duration_seconds=duration,
                    number_of_videos=1,
                    enhance_prompt=True,
                ),
            )

            # 等待完成（与上面相同的逻辑）
            max_wait_time = 600
            wait_time = 0
            poll_interval = 20

            while not operation.done and wait_time < max_wait_time:
                print(f"等待视频生成中... ({wait_time}/{max_wait_time}秒)")
                time.sleep(poll_interval)
                wait_time += poll_interval
                operation = self.client.operations.get(operation)

            if operation.done and hasattr(operation, 'response') and operation.response:
                generated_videos = operation.response.generated_videos
                if generated_videos and len(generated_videos) > 0:
                    video = generated_videos[0].video

                    timestamp = int(time.time())
                    video_filename = f"veo2_image_to_video_{timestamp}.mp4"
                    video_filepath = os.path.join(current_app.config['GENERATED_FOLDER'], video_filename)

                    try:
                        self.client.files.download(file=video)
                        video.save(video_filepath)

                        return {
                            'success': True,
                            'status': 'video_generated',
                            'message': '从图像生成视频成功！',
                            'video_path': video_filepath,
                            'source_image': image_path,
                            'original_prompt': prompt,
                            'optimized_prompt': optimized_prompt,
                            'duration': duration,
                            'aspect_ratio': aspect_ratio,
                            'model': 'Veo 2.0 Image-to-Video',
                        }, 200

                    except Exception as download_error:
                        return {
                            'success': False,
                            'error': f'视频保存失败: {str(download_error)}'
                        }, 500

            # 如果失败，返回制作方案
            return self._generate_enhanced_video_plan(optimized_prompt, duration, "image-to-video", aspect_ratio)

        except Exception as e:
            error_msg = f"图像到视频生成失败: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg
            }, 500

    def get_video_styles(self):
        """获取可用的视频风格选项"""
        return {
            'realistic': {
                'name': '写实风格',
                'description': '真实感强的视频风格，适合纪录片和现实场景',
                'keywords': 'photorealistic, natural lighting, documentary style'
            },
            'cinematic': {
                'name': '电影风格',
                'description': '电影级别的视觉效果，具有专业的摄影技巧',
                'keywords': 'cinematic, film noir, dramatic lighting, professional cinematography'
            },
            'artistic': {
                'name': '艺术风格',
                'description': '艺术化的创意风格，独特的美学表现',
                'keywords': 'artistic, creative, stylized, unique aesthetic'
            },
            'animation': {
                'name': '动画风格',
                'description': '动画风格的视频，适合卡通和创意内容',
                'keywords': '3D animation, cartoon style, animated, colorful'
            },
            'vintage': {
                'name': '复古风格',
                'description': '怀旧复古的视觉风格',
                'keywords': 'vintage, retro, classic, nostalgic, film grain'
            },
            'futuristic': {
                'name': '未来风格',
                'description': '科幻未来感的视觉效果',
                'keywords': 'futuristic, sci-fi, cyberpunk, neon, high-tech'
            }
        }

    def get_duration_options(self):
        """获取可用的时长选项"""
        return {
            5: "5秒 - 快速展示",
            6: "6秒 - 标准短视频",
            7: "7秒 - 详细展示",
            8: "8秒 - 完整叙述"
        }

    def get_aspect_ratio_options(self):
        """获取可用的宽高比选项"""
        return {
            "16:9": {
                'name': '横屏 (16:9)',
                'description': '适合电脑和电视观看，风景和宽幅场景',
                'use_case': '电影、风景、产品展示'
            },
            "9:16": {
                'name': '竖屏 (9:16)',
                'description': '适合手机观看，社交媒体短视频',
                'use_case': 'TikTok、Instagram Stories、手机视频'
            }
        }

    def _generate_enhanced_video_plan(self, prompt, duration, style, aspect_ratio):
        """
        生成增强的视频制作方案（当API不可用时的备选方案）
        """
        try:
            plan_prompt = f"""
作为专业的视频制作顾问，请为以下视频需求制定详细的制作方案：

视频描述：{prompt}
时长：{duration}秒
风格：{style}
宽高比：{aspect_ratio}

请提供以下内容：
1. 分镜头脚本（每秒的画面描述）
2. 摄影技巧建议（镜头运动、角度、构图）
3. 灯光和色彩方案
4. 后期制作建议
5. 设备和软件推荐
6. 预算估算
7. 制作时间安排
8. 可能的挑战和解决方案

请以专业且实用的方式组织这些信息。
"""

            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=plan_prompt
            )

            plan_content = response.text

            # 生成预览图
            preview_image_path = self._generate_preview_image(prompt, style)

            return {
                'success': True,
                'status': 'plan_generated',
                'message': 'Veo 2.0暂时不可用，已生成详细的视频制作方案',
                'video_plan': plan_content,
                'preview_image': preview_image_path,
                'original_prompt': prompt,
                'duration': duration,
                'style': style,
                'aspect_ratio': aspect_ratio,
                'note': '这是一个详细的制作方案，您可以使用专业视频制作软件来实现'
            }, 200

        except Exception as e:
            print(f"生成制作方案失败: {str(e)}")
            return {
                'success': False,
                'error': f'无法生成视频制作方案: {str(e)}'
            }, 500

    def _generate_preview_image(self, prompt, style):
        """生成预览图像"""
        try:
            # 使用Imagen生成预览图
            preview_prompt = f"A single frame preview of: {prompt}, {style} style, high quality, detailed"

            response = self.client.models.generate_images(
                model="imagen-3.0-generate-001",
                prompt=preview_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9"
                )
            )

            if response.generated_images:
                timestamp = int(time.time())
                preview_filename = f"video_preview_{timestamp}.png"
                preview_path = save_generated_image(
                    response.generated_images[0].image.image_bytes,
                    preview_filename,
                    current_app.config['GENERATED_FOLDER']
                )
                return preview_path

        except Exception as e:
            print(f"生成预览图失败: {str(e)}")

        return None


