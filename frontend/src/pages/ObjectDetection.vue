<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <!-- 页面标题 -->
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">目标检测</h1>
      <p class="text-gray-600">识别和定位图像中的物体，支持多种检测算法</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 左侧：上传和设置 -->
      <div class="space-y-6">
        <!-- 图像上传 -->
        <div class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-upload text-xl text-blue-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">上传图像</h2>
          </div>

          <DragUpload
            @file-selected="handleFileUpload"
            @file-cleared="clearImage"
            @error="handleUploadError"
            click-text="点击上传图像或拖拽文件到此区域"
            support-text="支持 JPG, PNG, GIF 格式"
          />
        </div>

        <!-- 检测设置 -->
        <div v-if="imagePreview" class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-cog text-xl text-green-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">检测设置</h2>
          </div>

          <div class="space-y-4">
            <!-- 检测方法 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">检测方法</label>
              <select v-model="detectionMethod" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent">
                <option value="gemini">Gemini AI 检测</option>
                <option value="opencv">OpenCV 检测</option>
                <option value="yolo">YOLO 检测</option>
                <option value="comparison">对比分析</option>
              </select>
            </div>

            <!-- OpenCV算法选择 -->
            <div v-if="detectionMethod === 'opencv'">
              <label class="block text-sm font-medium text-gray-700 mb-2">OpenCV算法</label>
              <select v-model="opencvMethod" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent">
                <option value="contour">轮廓检测</option>
                <option value="cascade">级联分类器</option>
                <option value="template">模板匹配</option>
                <option value="edge">边缘检测</option>
              </select>
            </div>

            <!-- YOLO模型选择 -->
            <div v-if="detectionMethod === 'yolo'">
              <label class="block text-sm font-medium text-gray-700 mb-2">YOLO模型</label>
              <select v-model="yoloModel" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent">
                <option v-for="(model, key) in availableYoloModels" :key="key" :value="key">
                  {{ model.name }}
                </option>
              </select>
              <p v-if="availableYoloModels[yoloModel]" class="text-sm text-gray-600 mt-1">
                {{ availableYoloModels[yoloModel].description }}
              </p>
            </div>

            <!-- 检测目标 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">检测目标</label>
              <input v-model="detectionTarget"
                     placeholder="请输入要检测的物体名称（可选）"
                     class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent">
              <p class="text-sm text-gray-600 mt-1">留空将检测所有可识别的物体</p>
            </div>

            <!-- 置信度阈值 -->
            <div v-if="detectionMethod === 'yolo'">
              <label class="block text-sm font-medium text-gray-700 mb-2">置信度阈值: {{ confidenceThreshold }}</label>
              <input type="range" v-model="confidenceThreshold" min="0.1" max="1.0" step="0.1" class="w-full">
            </div>
          </div>

          <button @click="detectObjects"
                  :disabled="loading"
                  class="w-full mt-6 bg-red-600 text-white py-3 px-6 rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
            <i v-if="loading" class="fas fa-spinner fa-spin mr-2"></i>
            {{ loading ? '检测中...' : '开始检测' }}
          </button>
        </div>
      </div>

      <!-- 右侧：结果显示 -->
      <div class="space-y-6">
        <!-- 检测结果 -->
        <div v-if="result" class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i :class="result.success ? 'fas fa-search text-xl text-green-500 mr-3' : 'fas fa-exclamation-triangle text-xl text-red-500 mr-3'"></i>
            <h2 class="text-lg font-semibold text-gray-900">{{ result.success ? '检测结果' : '检测提示' }}</h2>
          </div>

          <!-- 内容不匹配提示 -->
          <div v-if="!result.success && (result.explanation || result.suggestion || result.message)" class="mb-4 p-4 bg-red-50 border-2 border-red-200 rounded-lg shadow-md">
            <div class="flex items-start">
              <i class="fas fa-exclamation-triangle text-red-500 mt-1 mr-3 text-lg"></i>
              <div class="flex-1">
                <h3 class="font-medium text-red-800 mb-2 flex items-center">
                  <span>检测结果提示</span>
                  <span class="ml-2 px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">未匹配</span>
                </h3>
                <p v-if="result.explanation" class="text-red-700 mb-2 font-medium">{{ result.explanation }}</p>
                <p v-if="result.message" class="text-red-700 mb-2 font-medium">{{ result.message }}</p>
                <p v-if="result.suggestion" class="text-red-600 mb-2 text-sm">{{ result.suggestion }}</p>
                <div v-if="result.detected_objects && result.detected_objects.length > 0" class="mt-3 p-3 bg-white border border-red-100 rounded">
                  <p class="text-red-700 text-sm mb-2 font-medium">图像中检测到的对象：</p>
                  <div class="flex flex-wrap gap-1">
                    <span v-for="obj in result.detected_objects.slice(0, 5)" :key="obj.class_name || obj"
                          class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded border">
                      {{ obj.class_name || obj }}
                    </span>
                  </div>
                </div>
                <div v-if="result.alternative_queries && result.alternative_queries.length > 0" class="mt-3 p-3 bg-white border border-red-100 rounded">
                  <p class="text-red-700 text-sm mb-2 font-medium">建议搜索：</p>
                  <div class="flex flex-wrap gap-1">
                    <span v-for="query in result.alternative_queries.slice(0, 3)" :key="query"
                          class="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded cursor-pointer hover:bg-blue-200 transition-colors duration-200 border border-blue-200"
                          @click="detectionTarget = query">
                      {{ query }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 检测结果图像 -->
          <div v-if="result.summary_image" class="mb-4">
            <h3 class="font-medium text-gray-900 mb-2">检测结果汇总</h3>
            <img :src="getImageUrl(result.summary_image)"
                 class="w-full rounded-lg shadow-md border"
                 alt="检测结果汇总"
                 @error="handleImageError">
          </div>

          <!-- 单个边界框图像 -->
          <div v-if="result.bbox_images && result.bbox_images.length > 0" class="mb-4">
            <h3 class="font-medium text-gray-900 mb-2">检测到的对象 ({{ result.bbox_images.length }}个)</h3>
            <div class="space-y-3">
              <div v-for="(imagePath, index) in result.bbox_images" :key="index" class="border rounded-lg p-3 bg-gray-50">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm font-medium text-gray-700">
                    {{ result.detected_objects[index]?.label || `对象 ${index + 1}` }}
                  </span>
                  <span v-if="result.detected_objects[index]?.confidence" class="text-xs text-gray-500">
                    置信度: {{ Math.round(result.detected_objects[index].confidence * 100) }}%
                  </span>
                </div>
                <img :src="getImageUrl(imagePath)"
                     class="w-full max-w-md mx-auto rounded border"
                     :alt="`检测对象 ${index + 1}`"
                     @error="handleImageError">
              </div>
            </div>
          </div>

          <!-- 检测统计 - 只在成功检测时显示 -->
          <div v-if="result.success && result.detected_objects && result.detected_objects.length > 0" class="mb-4">
            <h3 class="font-medium text-gray-900 mb-2">检测到的物体 ({{ result.detected_objects.length }}个)</h3>
            <div class="space-y-2 max-h-40 overflow-y-auto">
              <div v-for="(obj, index) in result.detected_objects" :key="index"
                   class="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span class="text-gray-800">{{ obj.name || obj.label || obj.class_name }}</span>
                <span v-if="obj.confidence" class="text-sm text-gray-600">
                  {{ Math.round(obj.confidence * 100) }}%
                </span>
              </div>
            </div>
          </div>

          <!-- 对比分析结果 -->
          <div v-if="result.gemini_result || result.opencv_result || result.yolo_result" class="mb-4">
            <h3 class="font-medium text-gray-900 mb-4">检测方法对比分析</h3>

            <!-- 对比统计 -->
            <div v-if="result.comparison" class="mb-4 p-4 bg-gray-50 rounded-lg">
              <div class="flex items-center justify-between mb-3">
                <h4 class="font-medium text-gray-800">检测统计总览</h4>
                <div class="text-sm text-gray-600">
                  {{ result.comparison.successful_methods || 0 }}/{{ result.comparison.total_methods || 3 }} 方法成功
                </div>
              </div>

              <div class="grid grid-cols-3 gap-4 text-center mb-3">
                <div class="p-3 bg-white rounded border">
                  <div class="text-xl font-bold text-blue-600">{{ result.comparison.gemini_count || 0 }}</div>
                  <div class="text-sm text-gray-600">Gemini AI</div>
                </div>
                <div class="p-3 bg-white rounded border">
                  <div class="text-xl font-bold text-green-600">{{ result.comparison.opencv_count || 0 }}</div>
                  <div class="text-sm text-gray-600">OpenCV</div>
                </div>
                <div class="p-3 bg-white rounded border">
                  <div class="text-xl font-bold text-purple-600">{{ result.comparison.yolo_count || 0 }}</div>
                  <div class="text-sm text-gray-600">YOLO</div>
                </div>
              </div>

              <!-- 总结信息 -->
              <div class="text-center p-2 rounded"
                   :class="result.comparison.has_detections ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'">
                <i :class="result.comparison.has_detections ? 'fas fa-check-circle' : 'fas fa-info-circle'" class="mr-2"></i>
                <span v-if="result.comparison.has_detections">
                  成功检测到目标对象 "{{ result.object_name || detectionTarget }}"
                </span>
                <span v-else>
                  所有方法均未检测到目标对象 "{{ result.object_name || detectionTarget }}"
                </span>
              </div>
            </div>

            <!-- 详细结果展示 -->
            <div class="space-y-4">
              <!-- Gemini AI 结果 -->
              <div class="border border-blue-200 rounded-lg p-4 bg-blue-50">
                <div class="flex items-center justify-between mb-3">
                  <h4 class="font-medium text-blue-800 flex items-center">
                    <i class="fas fa-brain mr-2"></i>
                    Gemini AI 检测结果
                  </h4>
                  <span class="text-sm text-blue-600">
                    {{ result.gemini_result?.success ? '成功' : '失败' }}
                  </span>
                </div>

                <div v-if="result.gemini_result?.success">
                  <div v-if="result.gemini_result.detected_objects && result.gemini_result.detected_objects.length > 0">
                    <p class="text-sm text-blue-700 mb-2">检测到 {{ result.gemini_result.detected_objects.length }} 个对象：</p>
                    <div class="flex flex-wrap gap-1 mb-3">
                      <span v-for="obj in result.gemini_result.detected_objects" :key="obj.name || obj.label"
                            class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                        {{ obj.name || obj.label }}
                        <span v-if="obj.confidence" class="ml-1 opacity-75">
                          ({{ Math.round(obj.confidence * 100) }}%)
                        </span>
                      </span>
                    </div>
                    <!-- Gemini 检测结果图像 -->
                    <div v-if="result.gemini_result.summary_image || (result.gemini_result.bbox_images && result.gemini_result.bbox_images.length > 0)" class="mt-3">
                      <!-- 优先显示汇总图像 -->
                      <div v-if="result.gemini_result.summary_image">
                        <img :src="getImageUrl(result.gemini_result.summary_image)"
                             class="w-full max-w-sm mx-auto rounded border bg-white"
                             alt="Gemini 检测结果汇总"
                             @error="handleImageError">
                      </div>
                      <!-- 如果没有汇总图像，显示边界框图像 -->
                      <div v-else-if="result.gemini_result.bbox_images && result.gemini_result.bbox_images.length > 0">
                        <div v-if="result.gemini_result.bbox_images.length === 1">
                          <img :src="getImageUrl(result.gemini_result.bbox_images[0])"
                               class="w-full max-w-sm mx-auto rounded border bg-white"
                               alt="Gemini 检测结果"
                               @error="handleImageError">
                        </div>
                        <div v-else class="grid grid-cols-2 gap-2">
                          <img v-for="(imgPath, idx) in result.gemini_result.bbox_images.slice(0, 4)"
                               :key="idx"
                               :src="getImageUrl(imgPath)"
                               class="w-full rounded border bg-white"
                               :alt="`Gemini 检测结果 ${idx + 1}`"
                               @error="handleImageError">
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-sm text-blue-600">未检测到指定对象</div>
                </div>

                <div v-else class="p-3 bg-red-50 border border-red-200 rounded">
                  <div v-if="result.gemini_result?.message || result.gemini_result?.suggestion" class="text-sm">
                    <p v-if="result.gemini_result.message" class="text-red-700 mb-1 font-medium">{{ result.gemini_result.message }}</p>
                    <p v-if="result.gemini_result.suggestion" class="text-red-600 text-xs">{{ result.gemini_result.suggestion }}</p>
                    <div v-if="result.gemini_result.detected_objects && result.gemini_result.detected_objects.length > 0" class="mt-2">
                      <p class="text-red-600 text-xs mb-1">检测到的对象：</p>
                      <div class="flex flex-wrap gap-1">
                        <span v-for="obj in result.gemini_result.detected_objects.slice(0, 3)" :key="obj"
                              class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                          {{ obj }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-sm text-red-700">
                    {{ result.gemini_result?.error || '检测失败' }}
                  </div>
                </div>
              </div>

              <!-- OpenCV 结果 -->
              <div class="border border-green-200 rounded-lg p-4 bg-green-50">
                <div class="flex items-center justify-between mb-3">
                  <h4 class="font-medium text-green-800 flex items-center">
                    <i class="fas fa-eye mr-2"></i>
                    OpenCV 检测结果
                  </h4>
                  <span class="text-sm text-green-600">
                    {{ result.opencv_result?.success ? '成功' : '失败' }}
                  </span>
                </div>

                <div v-if="result.opencv_result?.success">
                  <div v-if="result.opencv_result.detected_objects && result.opencv_result.detected_objects.length > 0">
                    <p class="text-sm text-green-700 mb-2">检测到 {{ result.opencv_result.detected_objects.length }} 个对象：</p>
                    <div class="flex flex-wrap gap-1 mb-3">
                      <span v-for="obj in result.opencv_result.detected_objects" :key="obj.name || obj.label"
                            class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                        {{ obj.name || obj.label }}
                        <span v-if="obj.confidence" class="ml-1 opacity-75">
                          ({{ Math.round(obj.confidence * 100) }}%)
                        </span>
                      </span>
                    </div>
                    <!-- OpenCV 检测结果图像 -->
                    <div v-if="result.opencv_result.summary_image" class="mt-3">
                      <img :src="getImageUrl(result.opencv_result.summary_image)"
                           class="w-full max-w-sm mx-auto rounded border bg-white"
                           alt="OpenCV 检测结果"
                           @error="handleImageError">
                    </div>
                  </div>
                  <div v-else class="text-sm text-green-600">未检测到指定对象</div>
                </div>

                <div v-else class="text-sm text-red-600">
                  <div v-if="result.opencv_result?.message || result.opencv_result?.suggestion">
                    <p v-if="result.opencv_result.message" class="mb-1">{{ result.opencv_result.message }}</p>
                    <p v-if="result.opencv_result.suggestion" class="text-xs">{{ result.opencv_result.suggestion }}</p>
                  </div>
                  <div v-else>
                    {{ result.opencv_result?.error || '检测失败' }}
                  </div>
                </div>
              </div>

              <!-- YOLO 结果 -->
              <div class="border border-purple-200 rounded-lg p-4 bg-purple-50">
                <div class="flex items-center justify-between mb-3">
                  <h4 class="font-medium text-purple-800 flex items-center">
                    <i class="fas fa-search mr-2"></i>
                    YOLO 检测结果
                  </h4>
                  <span class="text-sm text-purple-600">
                    {{ result.yolo_result?.success ? '成功' : '失败' }}
                  </span>
                </div>

                <div v-if="result.yolo_result?.success">
                  <div v-if="result.yolo_result.detected_objects && result.yolo_result.detected_objects.length > 0">
                    <p class="text-sm text-purple-700 mb-2">检测到 {{ result.yolo_result.detected_objects.length }} 个对象：</p>
                    <div class="flex flex-wrap gap-1 mb-3">
                      <span v-for="obj in result.yolo_result.detected_objects" :key="obj.class_name || obj.name || obj.label"
                            class="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                        {{ obj.class_name || obj.name || obj.label }}
                        <span v-if="obj.confidence" class="ml-1 opacity-75">
                          ({{ Math.round(obj.confidence * 100) }}%)
                        </span>
                      </span>
                    </div>
                    <!-- YOLO 检测结果图像 -->
                    <div v-if="result.yolo_result.summary_image" class="mt-3">
                      <img :src="getImageUrl(result.yolo_result.summary_image)"
                           class="w-full max-w-sm mx-auto rounded border bg-white"
                           alt="YOLO 检测结果"
                           @error="handleImageError">
                    </div>
                  </div>
                  <div v-else class="text-sm text-purple-600">未检测到指定对象</div>
                </div>

                <div v-else class="text-sm text-red-600">
                  <div v-if="result.yolo_result?.message || result.yolo_result?.suggestion">
                    <p v-if="result.yolo_result.message" class="mb-1">{{ result.yolo_result.message }}</p>
                    <p v-if="result.yolo_result.suggestion" class="text-xs">{{ result.yolo_result.suggestion }}</p>
                    <div v-if="result.yolo_result.alternative_queries && result.yolo_result.alternative_queries.length > 0" class="mt-2">
                      <p class="text-xs text-purple-600 mb-1">建议搜索：</p>
                      <div class="flex flex-wrap gap-1">
                        <span v-for="query in result.yolo_result.alternative_queries.slice(0, 3)" :key="query"
                              class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded cursor-pointer hover:bg-blue-200"
                              @click="detectionTarget = query">
                          {{ query }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div v-else>
                    {{ result.yolo_result?.error || '检测失败' }}
                  </div>
                </div>
              </div>

              <!-- 对比分析汇总图像 -->
              <div v-if="result.comparison && (
                (result.gemini_result?.summary_image) ||
                result.opencv_result?.summary_image ||
                result.yolo_result?.summary_image
              )" class="mt-6">
                <h4 class="font-medium text-gray-900 mb-4 flex items-center">
                  <i class="fas fa-images mr-2"></i>
                  所有检测结果对比
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <!-- Gemini 结果图像 -->
                  <div v-if="result.gemini_result?.summary_image" class="text-center">
                    <h5 class="text-sm font-medium text-blue-700 mb-2">Gemini AI 检测结果</h5>
                    <img :src="getImageUrl(result.gemini_result.summary_image)"
                         class="w-full rounded border bg-white shadow-sm"
                         alt="Gemini 检测结果"
                         @error="handleImageError">
                  </div>

                  <!-- OpenCV 结果图像 -->
                  <div v-if="result.opencv_result?.summary_image" class="text-center">
                    <h5 class="text-sm font-medium text-green-700 mb-2">OpenCV 检测结果</h5>
                    <img :src="getImageUrl(result.opencv_result.summary_image)"
                         class="w-full rounded border bg-white shadow-sm"
                         alt="OpenCV 检测结果"
                         @error="handleImageError">
                  </div>

                  <!-- YOLO 结果图像 -->
                  <div v-if="result.yolo_result?.summary_image" class="text-center">
                    <h5 class="text-sm font-medium text-purple-700 mb-2">YOLO 检测结果</h5>
                    <img :src="getImageUrl(result.yolo_result.summary_image)"
                         class="w-full rounded border bg-white shadow-sm"
                         alt="YOLO 检测结果"
                         @error="handleImageError">
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 检测信息 -->
          <div class="text-sm text-gray-600 space-y-1">
            <p><strong>检测方法：</strong>{{ getMethodName(detectionMethod) }}</p>
            <p v-if="result.processing_time"><strong>处理时间：</strong>{{ result.processing_time }}秒</p>
            <p v-if="detectionTarget"><strong>检测目标：</strong>{{ detectionTarget }}</p>
          </div>
        </div>

        <!-- 使用说明 -->
        <div v-if="!result" class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-info-circle text-xl text-blue-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">使用说明</h2>
          </div>
          <div class="space-y-3 text-gray-600">
            <div class="flex items-start">
              <span class="bg-red-100 text-red-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">1</span>
              <p>上传包含物体的图像文件</p>
            </div>
            <div class="flex items-start">
              <span class="bg-red-100 text-red-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">2</span>
              <p>选择检测方法和设置参数</p>
            </div>
            <div class="flex items-start">
              <span class="bg-red-100 text-red-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">3</span>
              <p>可选择指定要检测的物体类型</p>
            </div>
            <div class="flex items-start">
              <span class="bg-red-100 text-red-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">4</span>
              <p>点击"开始检测"查看结果</p>
            </div>
          </div>

          <div class="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div class="flex items-start">
              <i class="fas fa-lightbulb text-yellow-600 mt-1 mr-3"></i>
              <div class="text-yellow-800">
                <p class="font-medium mb-1">检测方法说明：</p>
                <ul class="text-sm space-y-1">
                  <li><strong>Gemini AI：</strong>使用Google AI进行智能物体识别</li>
                  <li><strong>OpenCV：</strong>传统计算机视觉算法</li>
                  <li><strong>YOLO：</strong>实时物体检测神经网络</li>
                  <li><strong>对比分析：</strong>同时使用多种方法并对比结果</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/services/api'
import DragUpload from '@/components/DragUpload.vue'

export default {
  name: 'ObjectDetection',
  components: {
    DragUpload
  },
  setup() {
    const selectedFile = ref(null)
    const imagePreview = ref('')
    const detectionMethod = ref('gemini')
    const detectionTarget = ref('')
    const opencvMethod = ref('contour')
    const yoloModel = ref('yolo11n')
    const confidenceThreshold = ref(0.5)
    const loading = ref(false)
    const result = ref(null)
    const fileInput = ref(null)
    const availableYoloModels = ref({
      'yolo11n': { name: 'YOLOv11 Nano', description: '最快的模型，适合实时检测' },
      'yolo11s': { name: 'YOLOv11 Small', description: '平衡速度和精度' },
      'yolo11m': { name: 'YOLOv11 Medium', description: '中等精度，适合大多数场景' },
      'yolo11l': { name: 'YOLOv11 Large', description: '高精度模型' },
      'yolo11x': { name: 'YOLOv11 Extra Large', description: '最高精度，速度较慢' }
    })

    // 加载YOLO模型列表
    const loadYoloModels = async () => {
      try {
        const response = await api.get('/object-detection/yolo-models')
        if (response.data.success) {
          availableYoloModels.value = response.data.models
        }
      } catch (error) {
        console.error('加载YOLO模型失败:', error)
        // 静默处理，不显示错误消息，因为这不是用户主动操作
      }
    }

    const handleFileUpload = (file) => {
      if (file) {
        selectedFile.value = file
        const reader = new FileReader()
        reader.onload = (e) => {
          imagePreview.value = e.target.result
        }
        reader.readAsDataURL(file)
        result.value = null
      }
    }

    const handleUploadError = (errorMessage) => {
      ElMessage.error(errorMessage)
    }

    const clearImage = () => {
      selectedFile.value = null
      imagePreview.value = ''
      result.value = null
    }

    const detectObjects = async () => {
      if (!selectedFile.value) {
        ElMessage.warning('请选择图像文件')
        return
      }

      if (!detectionTarget.value.trim()) {
        ElMessage.warning('请输入要检测的对象名称')
        return
      }

      loading.value = true
      result.value = null

      try {
        const formData = new FormData()
        formData.append('image', selectedFile.value)
        formData.append('object_name', detectionTarget.value.trim())

        let endpoint = '/object-detection'

        if (detectionMethod.value === 'opencv') {
          endpoint = '/object-detection/opencv'
          formData.append('method', opencvMethod.value)
        } else if (detectionMethod.value === 'yolo') {
          endpoint = '/object-detection/yolo'
          formData.append('model', yoloModel.value)
          formData.append('confidence', confidenceThreshold.value)
        } else if (detectionMethod.value === 'comparison') {
          endpoint = '/object-detection/compare'
          formData.append('opencv_method', opencvMethod.value)
          formData.append('yolo_model', yoloModel.value)
        }

        const response = await api.post(endpoint, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        if (response.data.success) {
          result.value = response.data
          ElMessage.success('检测完成！')
        } else {
          // 处理内容不匹配的情况
          if (response.data.explanation || response.data.suggestion || response.data.message || response.data.detected_objects) {
            result.value = response.data
            ElMessage.error(response.data.error || response.data.message || '检测失败')
          } else {
            throw new Error(response.data.error || '检测失败')
          }
        }
      } catch (error) {
        console.error('检测失败:', error)

        // 优先显示后端返回的友好错误信息
        let errorMessage = error.message || '检测失败，请重试'

        // 如果有建议信息，添加到错误消息中
        if (error.suggestion) {
          errorMessage += `\n建议：${error.suggestion}`
        }

        // 检查是否有特殊的检测结果数据（即使失败也可能有部分结果）
        if (error.backendError && (error.backendError.explanation || error.backendError.detected_objects)) {
          result.value = error.backendError
          ElMessage.warning(errorMessage)
        } else {
          ElMessage.error(errorMessage)
        }
      } finally {
        loading.value = false
      }
    }

    const getImageUrl = (imagePath) => {
      if (!imagePath) return ''

      // 如果是完整的URL，直接返回
      if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
        return imagePath
      }

      // 如果已经是正确的相对路径格式，直接返回
      if (imagePath.startsWith('/storage/generated/')) {
        return imagePath
      }

      // 如果包含完整路径（Windows或Linux），提取文件名
      if (imagePath.includes('storage') && (imagePath.includes('generated') || imagePath.includes('\\'))) {
        const filename = imagePath.split(/[/\\]/).pop()
        return `/storage/generated/${filename}`
      }

      // 如果只是文件名，构建完整路径
      if (!imagePath.includes('/') && !imagePath.includes('\\')) {
        return `/storage/generated/${imagePath}`
      }

      // 默认情况：清理路径并构建
      const filename = imagePath.split(/[/\\]/).pop()
      return `/storage/generated/${filename}`
    }

    const getMethodName = (method) => {
      const methodNames = {
        'gemini': 'Gemini AI',
        'opencv': 'OpenCV',
        'yolo': 'YOLO',
        'comparison': '对比分析'
      }
      return methodNames[method] || method
    }

    const handleImageError = (event) => {
      console.error('图像加载失败:', event.target.src)
      event.target.style.display = 'none'
    }

    onMounted(() => {
      loadYoloModels()
    })

    return {
      selectedFile,
      imagePreview,
      detectionMethod,
      detectionTarget,
      opencvMethod,
      yoloModel,
      confidenceThreshold,
      loading,
      result,
      availableYoloModels,
      handleFileUpload,
      handleUploadError,
      clearImage,
      detectObjects,
      getImageUrl,
      getMethodName,
      handleImageError
    }
  }
}
</script>

<style scoped>
/* 组件特定样式 */
</style>
