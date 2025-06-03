import os
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont
import time
from flask import current_app
from ..utils.helpers import allowed_file, save_uploaded_file

class YOLODetectionService:
    """YOLO目标检测服务"""

    def __init__(self):
        self.models = {
            'yolo11n': None,  # YOLOv11 nano
            'yolo11s': None,  # YOLOv11 small
            'yolo11m': None,  # YOLOv11 medium
            'yolo11l': None,  # YOLOv11 large
            'yolo11x': None,  # YOLOv11 extra large
        }
        self.current_model = None
        self.current_model_name = None

    def load_model(self, model_name='yolo11n'):
        """加载YOLO模型"""
        try:
            if model_name not in self.models:
                model_name = 'yolo11n'  # 默认使用nano版本

            if self.models[model_name] is None:
                # 使用配置中定义的模型目录
                models_folder = current_app.config.get('MODELS_FOLDER')
                if models_folder:
                    model_path = os.path.join(models_folder, f'{model_name}.pt')
                else:
                    # 回退到当前目录
                    model_path = f'{model_name}.pt'

                if os.path.exists(model_path):
                    print(f"找到本地模型文件: {model_path}")
                    print(f"正在加载 {model_name} 模型...")
                    self.models[model_name] = YOLO(model_path)
                    print(f"{model_name} 模型加载完成")
                else:
                    print(f"本地未找到模型文件: {model_path}")
                    print(f"正在下载并加载 {model_name} 模型...")
                    # 如果本地没有，先尝试下载到模型目录
                    if models_folder and os.path.exists(models_folder):
                        # 下载到指定的模型目录
                        self.models[model_name] = YOLO(f'{model_name}.pt')  # 先下载
                        # 然后移动到正确位置（如果需要）
                        downloaded_path = f'{model_name}.pt'
                        if os.path.exists(downloaded_path) and downloaded_path != model_path:
                            import shutil
                            shutil.move(downloaded_path, model_path)
                            print(f"模型文件已移动到: {model_path}")
                        self.models[model_name] = YOLO(model_path)
                    else:
                        self.models[model_name] = YOLO(f'{model_name}.pt')  # 这会自动下载
                    print(f"{model_name} 模型下载并加载完成")

            self.current_model = self.models[model_name]
            self.current_model_name = model_name
            return True

        except Exception as e:
            print(f"加载YOLO模型失败: {str(e)}")
            return False

    def detect_objects(self, image_path, model_name='yolo11n', confidence=0.5, user_query=None):
        """使用YOLO检测图像中的对象"""
        try:
            # 加载模型
            if not self.load_model(model_name):
                return {
                    'success': False,
                    'error': f'无法加载YOLO模型: {model_name}'
                }

            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                return {
                    'success': False,
                    'error': '无法读取图像文件'
                }

            # 如果提供了用户查询，验证内容匹配性
            if user_query:
                content_match_result = self._validate_content_match(image_path, user_query)
                if not content_match_result['is_match']:
                    return {
                        'success': False,
                        'error': f'未检测到目标：{user_query}',
                        'message': f'图像中检测到的对象与您查询的"{user_query}"不匹配。{content_match_result["message"]}',
                        'suggestion': content_match_result.get('suggestion', '请检查图像内容或修改查询词汇。'),
                        'detected_objects': content_match_result.get('detected_objects', []),
                        'alternative_queries': content_match_result.get('alternative_queries', [])
                    }

            # 进行检测
            results = self.current_model(image, conf=confidence)

            # 处理检测结果
            detected_objects = []
            bbox_images = []

            # 创建汇总图像
            summary_image = image.copy()

            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for i, box in enumerate(boxes):
                        # 获取边界框坐标
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

                        # 获取类别和置信度
                        class_id = int(box.cls[0])
                        confidence_score = float(box.conf[0])
                        class_name = self.current_model.names[class_id]

                        # 添加到检测结果
                        detected_objects.append({
                            'label': class_name,
                            'confidence': confidence_score,
                            'bbox': [int(x1), int(y1), int(x2), int(y2)]
                        })

                        # 在汇总图像上绘制边界框
                        cv2.rectangle(summary_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

                        # 添加标签
                        label_text = f"{class_name}: {confidence_score:.2f}"
                        cv2.putText(summary_image, label_text, (x1, y1-10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                        # 创建单个对象的边界框图像
                        bbox_image = image[y1:y2, x1:x2].copy()

                        # 保存边界框图像
                        timestamp = int(time.time() * 1000)
                        bbox_filename = f"yolo_bbox_{timestamp}_{i}_{os.path.basename(image_path)}"
                        bbox_path = os.path.join(current_app.config['GENERATED_FOLDER'], bbox_filename)
                        cv2.imwrite(bbox_path, bbox_image)
                        bbox_images.append(bbox_path)

            # 保存汇总图像
            if detected_objects:
                timestamp = int(time.time() * 1000)
                summary_filename = f"yolo_summary_{timestamp}_{os.path.basename(image_path)}"
                summary_path = os.path.join(current_app.config['GENERATED_FOLDER'], summary_filename)
                cv2.imwrite(summary_path, summary_image)

                # 使用统一的URL生成函数
                from ..utils.helpers import get_image_url
                relative_bbox_images = [get_image_url(os.path.basename(img), 'generated') for img in bbox_images]
                relative_summary_image = get_image_url(os.path.basename(summary_path), 'generated')

                return {
                    'success': True,
                    'detected_objects': detected_objects,
                    'bbox_images': relative_bbox_images,
                    'summary_image': relative_summary_image,
                    'method': f'YOLO {model_name}',
                    'model_name': model_name,
                    'total_objects': len(detected_objects)
                }
            else:
                return {
                    'success': False,
                    'error': '未检测到任何对象',
                    'method': f'YOLO {model_name}',
                    'detected_objects': [],
                    'total_objects': 0
                }

        except Exception as e:
            print(f"YOLO检测错误: {str(e)}")
            return {
                'success': False,
                'error': f'YOLO检测失败: {str(e)}'
            }

    def _validate_content_match(self, image_path, user_query):
        """验证用户查询内容与图像内容的匹配性"""
        try:
            # 首先进行快速检测，获取图像中的对象
            if not self.load_model('yolo11n'):  # 使用最快的模型进行检测
                return {
                    'is_match': True,  # 如果无法加载模型，允许继续
                    'message': '无法验证内容匹配性，将继续处理'
                }

            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                return {
                    'is_match': True,
                    'message': '无法读取图像，将继续处理'
                }

            # 进行快速检测
            results = self.current_model(image, conf=0.25)  # 使用较低的置信度进行检测

            detected_objects = []
            for result in results:
                if result.boxes is not None:
                    classes = result.boxes.cls.cpu().numpy()
                    confidences = result.boxes.conf.cpu().numpy()

                    for cls, conf in zip(classes, confidences):
                        class_name = self.current_model.names[int(cls)]
                        detected_objects.append({
                            'class_name': class_name,
                            'confidence': float(conf)
                        })

            if not detected_objects:
                return {
                    'is_match': False,
                    'message': '图像中未检测到任何对象',
                    'suggestion': '请上传包含清晰对象的图像',
                    'detected_objects': []
                }

            # 检查用户查询是否与检测到的对象匹配
            user_query_lower = user_query.lower().strip()
            detected_names = [obj['class_name'].lower() for obj in detected_objects]

            # 严格的关键词匹配，包括同义词
            matched_objects = []

            # 创建同义词映射
            synonym_map = self._get_synonym_map()

            # 获取用户查询的所有可能匹配词汇
            query_words = self._expand_query_words(user_query_lower, synonym_map)

            # 更严格的匹配逻辑
            for obj in detected_objects:
                class_name = obj['class_name'].lower()

                # 检查精确匹配和同义词匹配
                if self._is_strict_match(query_words, class_name, synonym_map):
                    matched_objects.append(obj['class_name'])

            is_match = len(matched_objects) > 0

            if is_match:
                return {
                    'is_match': True,
                    'message': f'检测到匹配的对象: {", ".join(set(matched_objects))}',
                    'detected_objects': detected_objects,
                    'matched_objects': list(set(matched_objects)),
                    'confidence': 'high' if len(matched_objects) > 1 else 'medium'
                }
            else:
                detected_names = [obj['class_name'] for obj in detected_objects[:5]]  # 只显示前5个
                suggestions = self._generate_suggestions(user_query_lower, detected_names, synonym_map)

                return {
                    'is_match': False,
                    'message': f'图像中检测到的对象({", ".join(detected_names)})与您的查询"{user_query}"不匹配',
                    'suggestion': suggestions,
                    'detected_objects': detected_objects,
                    'alternative_queries': self._suggest_alternative_queries(detected_names)
                }

        except Exception as e:
            print(f"YOLO内容匹配验证错误: {str(e)}")
            # 如果验证过程出错，允许继续处理
            return {
                'is_match': True,
                'message': f'内容匹配验证出错，将继续处理: {str(e)}'
            }

    def _get_synonym_map(self):
        """获取更完善的同义词映射表"""
        return {
            # 动物类 - 更详细的映射
            'cat': ['kitten', 'feline', '猫', '小猫', 'kitty', '猫咪', '喵', '猫猫'],
            'dog': ['puppy', 'canine', '狗', '小狗', 'doggy', '狗狗', '犬', '汪'],
            'bird': ['飞鸟', '鸟类', 'avian', '鸟儿', '小鸟'],
            'horse': ['马', 'equine', 'pony', '马匹', '小马'],
            'cow': ['cattle', '牛', 'bull', '奶牛', '母牛'],
            'sheep': ['羊', 'lamb', '绵羊', '小羊'],
            'elephant': ['大象', '象'],
            'bear': ['熊', '狗熊', '黑熊', '棕熊'],
            'zebra': ['斑马'],
            'giraffe': ['长颈鹿'],
            'lion': ['狮子', '雄狮', '母狮'],
            'tiger': ['老虎', '虎'],
            'monkey': ['猴子', '猴'],
            'rabbit': ['兔子', '小兔', '兔'],

            # 交通工具
            'car': ['automobile', 'vehicle', '汽车', '车辆', '轿车', '小车'],
            'truck': ['lorry', '卡车', '货车', '大车'],
            'bus': ['coach', '公交车', '巴士', '客车'],
            'motorcycle': ['motorbike', '摩托车', '机车', '摩托'],
            'bicycle': ['bike', '自行车', '单车', '脚踏车'],
            'train': ['火车', 'locomotive', '列车'],
            'airplane': ['plane', '飞机', 'aircraft', '客机'],
            'boat': ['ship', '船', '轮船', '小船'],

            # 人物
            'person': ['people', 'human', '人', '人类', 'man', 'woman', 'individual', '人物'],
            'child': ['kid', '孩子', '儿童', '小孩'],
            'baby': ['infant', '婴儿', '宝宝', '小宝宝'],

            # 物品
            'phone': ['mobile', 'cellphone', '手机', '电话', 'smartphone', '移动电话'],
            'laptop': ['computer', '笔记本', '电脑', 'notebook', '笔记本电脑'],
            'book': ['书', '书籍', '图书'],
            'bottle': ['瓶子', 'container', '水瓶'],
            'cup': ['mug', '杯子', '茶杯', '水杯'],
            'clock': ['时钟', '钟表', 'watch', '手表'],
            'tv': ['television', '电视', 'monitor', '电视机'],
            'remote': ['遥控器', 'controller', '遥控'],

            # 食物
            'apple': ['苹果'],
            'banana': ['香蕉'],
            'orange': ['橙子', '橘子', '桔子'],
            'pizza': ['比萨', '披萨'],
            'cake': ['蛋糕'],
            'sandwich': ['三明治'],
            'donut': ['甜甜圈', '油炸圈饼'],

            # 家具
            'chair': ['椅子', '座椅'],
            'couch': ['sofa', '沙发'],
            'bed': ['床', '床铺'],
            'dining table': ['table', '桌子', '餐桌', '饭桌'],
            'toilet': ['厕所', '马桶', '卫生间'],

            # 运动用品
            'sports ball': ['ball', '球', '运动球'],
            'tennis racket': ['tennis', '网球拍', '球拍'],
            'baseball bat': ['棒球棒', '球棒'],
            'baseball glove': ['棒球手套', '手套'],
            'skateboard': ['滑板'],
            'surfboard': ['冲浪板'],
            'ski': ['滑雪板'],

            # 厨房用品
            'knife': ['刀', '小刀', '菜刀'],
            'spoon': ['勺子', '汤匙', '勺'],
            'fork': ['叉子', '餐叉'],
            'bowl': ['碗', '饭碗'],
            'wine glass': ['酒杯', '红酒杯', '玻璃杯'],
            'refrigerator': ['冰箱', 'fridge'],
            'microwave': ['微波炉'],
            'oven': ['烤箱'],
            'toaster': ['烤面包机'],

            # 电子设备
            'keyboard': ['键盘'],
            'mouse': ['鼠标'],
            'cell phone': ['phone', '手机', 'mobile', '移动电话'],

            # 植物和自然
            'flower': ['花', '花朵', '鲜花'],
            'tree': ['树', '树木', '大树'],
            'grass': ['草', '草地', '草坪'],

            # 建筑和结构
            'building': ['建筑', '房子', '楼房', '大楼'],
            'house': ['房子', '住宅', '房屋'],
            'bridge': ['桥', '大桥', '桥梁'],
        }

    def _expand_query_words(self, query, synonym_map):
        """扩展查询词汇，包括同义词"""
        words = [query] + query.split()
        expanded_words = set(words)

        for word in words:
            for key, synonyms in synonym_map.items():
                if word in synonyms or word == key:
                    expanded_words.add(key)
                    expanded_words.update(synonyms)

        return list(expanded_words)

    def _is_strict_match(self, query_words, class_name, synonym_map):
        """检查是否为严格匹配（包括同义词）"""
        # 1. 直接精确匹配
        for query_word in query_words:
            if query_word == class_name:
                return True

        # 2. 同义词精确匹配
        for query_word in query_words:
            # 检查查询词是否是检测类别的同义词
            for key, synonyms in synonym_map.items():
                if key == class_name and query_word in synonyms:
                    return True
                if query_word == key and class_name in synonyms:
                    return True

        # 3. 严格的部分匹配（仅限于特定情况）
        for query_word in query_words:
            if len(query_word) > 4:  # 只对较长的词进行部分匹配
                # 检查是否为复合词的一部分
                if (query_word in class_name and len(query_word) / len(class_name) > 0.6) or \
                   (class_name in query_word and len(class_name) / len(query_word) > 0.6):
                    return True

        return False

    def _generate_suggestions(self, user_query, detected_names, synonym_map):
        """生成建议"""
        suggestions = []

        # 基于检测到的对象生成建议
        if detected_names:
            suggestions.append(f"图像中包含: {', '.join(detected_names)}")
            suggestions.append(f"您可以尝试搜索: {', '.join(detected_names[:3])}")

        # 基于同义词生成建议
        for key, synonyms in synonym_map.items():
            if user_query in synonyms:
                suggestions.append(f"您搜索的是'{user_query}'，请尝试使用'{key}'")
                break

        return '; '.join(suggestions) if suggestions else "请检查图像内容或修改查询词汇"

    def _suggest_alternative_queries(self, detected_names):
        """建议替代查询词汇"""
        if not detected_names:
            return []

        # 返回检测到的对象名称作为建议
        return detected_names[:5]  # 最多返回5个建议

    def get_available_models(self):
        """获取可用的YOLO模型列表"""
        return {
            'yolo11n': {
                'name': 'YOLOv11 Nano',
                'description': '最快速度，较小精度',
                'size': '~6MB'
            },
            'yolo11s': {
                'name': 'YOLOv11 Small',
                'description': '平衡速度和精度',
                'size': '~22MB'
            },
            'yolo11m': {
                'name': 'YOLOv11 Medium',
                'description': '中等速度，较高精度',
                'size': '~50MB'
            },
            'yolo11l': {
                'name': 'YOLOv11 Large',
                'description': '较慢速度，高精度',
                'size': '~144MB'
            },
            'yolo11x': {
                'name': 'YOLOv11 Extra Large',
                'description': '最高精度，最慢速度',
                'size': '~218MB'
            }
        }

    def compare_with_opencv(self, image_path, opencv_result, yolo_model='yolo11n', confidence=0.5):
        """与OpenCV检测结果进行对比"""
        try:
            # 获取YOLO检测结果
            yolo_result = self.detect_objects(image_path, yolo_model, confidence)

            # 构建对比结果
            comparison_result = {
                'success': True,
                'yolo_result': yolo_result,
                'opencv_result': opencv_result,
                'comparison': {
                    'yolo_count': yolo_result.get('total_objects', 0) if yolo_result.get('success') else 0,
                    'opencv_count': len(opencv_result.get('detected_objects', [])) if opencv_result.get('success') else 0,
                    'yolo_model': yolo_model,
                    'opencv_method': opencv_result.get('method', 'OpenCV')
                }
            }

            return comparison_result

        except Exception as e:
            print(f"YOLO对比检测错误: {str(e)}")
            return {
                'success': False,
                'error': f'YOLO对比检测失败: {str(e)}'
            }

    def detect_objects_with_file(self, file, model_name='yolo11n', confidence=0.5, user_query=None):
        """使用文件对象进行YOLO检测"""
        try:
            if not file or not hasattr(file, 'filename') or file.filename == '':
                return {'success': False, 'error': '未选择文件'}, 400
            if not allowed_file(file.filename):
                return {'success': False, 'error': '无效的文件类型'}, 400

            # 检查是否是已经存在的文件路径（用于测试）
            if hasattr(file, 'filepath') and os.path.exists(file.filepath):
                filepath = file.filepath
            else:
                # 标准的Flask文件上传对象
                filepath = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])

            # 调用检测方法
            return self.detect_objects(filepath, model_name, confidence, user_query), 200

        except Exception as e:
            return {'success': False, 'error': f'YOLO检测失败: {str(e)}'}, 500

    def detect_objects_with_file_data(self, image_data, model_name='yolo11n', confidence=0.5, user_query=None):
        """使用base64图像数据进行YOLO检测"""
        try:
            import base64
            import tempfile

            # 处理base64图像数据
            image_data_clean = image_data.split(',')[1] if ',' in image_data else image_data
            image_bytes = base64.b64decode(image_data_clean)

            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(image_bytes)
                filepath = tmp_file.name

            # 调用检测方法
            result = self.detect_objects(filepath, model_name, confidence, user_query)

            # 清理临时文件
            import os
            try:
                os.unlink(filepath)
            except:
                pass

            return result, 200

        except Exception as e:
            return {'success': False, 'error': f'YOLO检测失败: {str(e)}'}, 500
