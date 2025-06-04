<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <!-- 页面标题 -->
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">图像分割</h1>
      <p class="text-gray-600">精确分割图像中的不同区域和对象</p>
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

          <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
            <input type="file" @change="handleFileUpload" accept="image/*" class="hidden" ref="fileInput">
            <div v-if="!imagePreview" @click="$refs.fileInput.click()" class="cursor-pointer">
              <i class="fas fa-cloud-upload-alt text-4xl text-gray-400 mb-4"></i>
              <p class="text-gray-600 mb-2">点击上传图像</p>
              <p class="text-sm text-gray-500">支持 JPG, PNG, GIF 格式</p>
            </div>
            <div v-else class="relative">
              <img :src="imagePreview" class="max-w-full h-80 object-contain mx-auto rounded-lg">
              <button @click="clearImage" class="absolute top-2 right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm hover:bg-red-600">
                ×
              </button>
            </div>
          </div>
        </div>

        <!-- 分割设置 -->
        <div v-if="imagePreview" class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-cog text-xl text-yellow-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">分割设置</h2>
          </div>

          <div class="space-y-4">
            <!-- 分割方法 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">分割方法</label>
              <select v-model="segmentationMethod" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent">
                <option value="gemini">Gemini AI 分割</option>
                <option value="opencv">OpenCV 分割</option>
                <option value="yolo">YOLO 分割</option>
                <option value="comparison">对比分析</option>
              </select>
            </div>

            <!-- 分割目标 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">分割目标</label>
              <input v-model="segmentationTarget"
                     placeholder="请输入要分割的物体名称（可选）"
                     class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent">
              <p class="text-sm text-gray-600 mt-1">留空将分割所有可识别的区域</p>
            </div>

            <!-- OpenCV分割算法 -->
            <div v-if="segmentationMethod === 'opencv'">
              <label class="block text-sm font-medium text-gray-700 mb-2">分割算法</label>
              <select v-model="opencvAlgorithm" class="w-full p-3 border border-gray-300 rounded-lg">
                <option value="watershed">分水岭算法</option>
                <option value="grabcut">GrabCut算法</option>
                <option value="kmeans">K-means聚类</option>
                <option value="threshold">阈值分割</option>
              </select>
            </div>

            <!-- YOLO模型选择 -->
            <div v-if="segmentationMethod === 'yolo'">
              <label class="block text-sm font-medium text-gray-700 mb-2">YOLO模型</label>
              <select v-model="yoloModel" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent">
                <option v-for="(model, key) in availableYoloModels" :key="key" :value="key">
                  {{ model.name }}
                </option>
              </select>
              <p v-if="availableYoloModels[yoloModel]" class="text-sm text-gray-600 mt-1">
                {{ availableYoloModels[yoloModel].description }}
              </p>
            </div>

            <!-- 置信度阈值 -->
            <div v-if="segmentationMethod === 'yolo'">
              <label class="block text-sm font-medium text-gray-700 mb-2">置信度阈值: {{ confidenceThreshold }}</label>
              <input type="range" v-model="confidenceThreshold" min="0.1" max="1.0" step="0.1" class="w-full">
            </div>
          </div>

          <button @click="segmentImage"
                  :disabled="loading"
                  class="w-full mt-6 bg-yellow-600 text-white py-3 px-6 rounded-lg hover:bg-yellow-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
            <i v-if="loading" class="fas fa-spinner fa-spin mr-2"></i>
            {{ loading ? '分割中...' : '开始分割' }}
          </button>
        </div>
      </div>

      <!-- 右侧：结果显示 -->
      <div class="space-y-6">
        <!-- 分割结果 -->
        <div v-if="result" class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i :class="result.success ? 'fas fa-cut text-xl text-green-500 mr-3' : 'fas fa-exclamation-triangle text-xl text-red-500 mr-3'"></i>
            <h2 class="text-lg font-semibold text-gray-900">{{ result.success ? '分割结果' : '分割提示' }}</h2>
          </div>

          <!-- 内容不匹配提示 -->
          <div v-if="!result.success && (result.explanation || result.suggestion || result.content_mismatch || result.message)" class="mb-4 p-4 bg-red-50 border-2 border-red-200 rounded-lg shadow-md">
            <div class="flex items-start">
              <i class="fas fa-exclamation-triangle text-red-500 mt-1 mr-3 text-lg"></i>
              <div class="flex-1">
                <h3 class="font-medium text-red-800 mb-2 flex items-center">
                  <span>分割结果提示</span>
                  <span class="ml-2 px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">未匹配</span>
                </h3>
                <p v-if="result.explanation" class="text-red-700 mb-2 font-medium">{{ result.explanation }}</p>
                <p v-if="result.message" class="text-red-700 mb-2 font-medium">{{ result.message }}</p>
                <p v-if="result.suggestion" class="text-red-600 mb-2 text-sm">{{ result.suggestion }}</p>
                <div v-if="result.detected_objects && result.detected_objects.length > 0" class="mt-3 p-3 bg-white border border-red-100 rounded">
                  <p class="text-red-700 text-sm mb-2 font-medium">图像中检测到的对象：</p>
                  <div class="flex flex-wrap gap-1">
                    <span v-for="obj in result.detected_objects.slice(0, 5)" :key="obj"
                          class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded border">
                      {{ obj }}
                    </span>
                  </div>
                </div>
                <div v-if="result.alternative_queries && result.alternative_queries.length > 0" class="mt-3 p-3 bg-white border border-red-100 rounded">
                  <p class="text-red-700 text-sm mb-2 font-medium">建议尝试分割：</p>
                  <div class="flex flex-wrap gap-1">
                    <span v-for="query in result.alternative_queries" :key="query"
                          class="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded cursor-pointer hover:bg-blue-200 transition-colors duration-200 border border-blue-200"
                          @click="segmentationTarget = query">
                      {{ query }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 分割结果图像 -->
          <div v-if="result.result_image_path || result.summary_image" class="mb-4">
            <h3 class="font-medium text-gray-900 mb-2">分割结果汇总</h3>
            <img :src="getImageUrl(result.result_image_path || result.summary_image)"
                 class="w-full rounded-lg shadow-md border"
                 alt="分割结果汇总"
                 @error="handleImageError">
          </div>

          <!-- 分割区域 -->
          <div v-if="result.segmented_objects && result.segmented_objects.length > 0" class="mb-4">
            <h3 class="font-medium text-gray-900 mb-3">分割区域 ({{ result.segmented_objects.length }}个)</h3>
            <div class="space-y-4 max-h-[600px] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
              <div v-for="(segment, index) in result.segmented_objects" :key="index"
                   class="border rounded-lg p-4 bg-gray-50">
                <div class="flex items-center justify-between mb-3">
                  <span class="text-sm font-medium text-gray-700">
                    {{ segment.name || segment.label || `分割区域 ${index + 1}` }}
                  </span>
                  <span v-if="segment.confidence" class="text-xs text-gray-500">
                    置信度: {{ Math.round(segment.confidence * 100) }}%
                  </span>
                </div>
                <div v-if="segment.description" class="text-xs text-gray-600 mb-2">
                  {{ segment.description }}
                </div>
                <img v-if="segment.segment_image || segment.image_path"
                     :src="getImageUrl(segment.segment_image || segment.image_path)"
                     class="w-full max-w-xs mx-auto rounded border bg-white"
                     :alt="`分割区域 ${index + 1}`"
                     @error="handleImageError">
                <div v-else class="w-full h-24 bg-gray-200 rounded border flex items-center justify-center">
                  <span class="text-gray-500 text-sm">图像加载失败</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 对比分析结果 -->
          <div v-if="result.gemini_result || result.opencv_result || result.yolo_result" class="mb-4">
            <h3 class="font-medium text-gray-900 mb-4">分割方法对比分析</h3>

            <!-- 对比统计 -->
            <div v-if="result.comparison" class="mb-4 p-4 bg-gray-50 rounded-lg">
              <div class="flex items-center justify-between mb-3">
                <h4 class="font-medium text-gray-800">分割统计总览</h4>
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
                   :class="result.comparison.has_segmentations ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'">
                <i :class="result.comparison.has_segmentations ? 'fas fa-check-circle' : 'fas fa-info-circle'" class="mr-2"></i>
                <span v-if="result.comparison.has_segmentations">
                  成功分割目标对象 "{{ result.object_name || segmentationTarget }}"
                </span>
                <span v-else>
                  所有方法均未分割到目标对象 "{{ result.object_name || segmentationTarget }}"
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
                    Gemini AI 分割结果
                  </h4>
                  <span class="text-sm text-blue-600">
                    {{ result.gemini_result?.success ? '成功' : '失败' }}
                  </span>
                </div>

                <div v-if="result.gemini_result?.success">
                  <div v-if="result.gemini_result.segmented_objects && result.gemini_result.segmented_objects.length > 0">
                    <p class="text-sm text-blue-700 mb-3">分割到 {{ result.gemini_result.segmented_objects.length }} 个区域：</p>

                    <!-- 分割区域标签 -->
                    <div class="flex flex-wrap gap-1 mb-3">
                      <span v-for="obj in result.gemini_result.segmented_objects" :key="obj.label"
                            class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                        {{ obj.label }}
                        <span v-if="obj.confidence" class="ml-1 opacity-75">
                          ({{ Math.round(obj.confidence * 100) }}%)
                        </span>
                      </span>
                    </div>

                    <!-- 分割结果图像 -->
                    <div class="grid grid-cols-2 gap-2">
                      <div v-for="(obj, index) in result.gemini_result.segmented_objects" :key="index"
                           class="border rounded p-2 bg-white">
                        <div class="text-xs text-blue-700 mb-1 font-medium">{{ obj.label }}</div>
                        <img v-if="obj.segment_image"
                             :src="getImageUrl(obj.segment_image)"
                             class="w-full h-24 object-contain rounded border"
                             :alt="obj.label"
                             @error="handleImageError">
                        <div v-else class="w-full h-24 bg-gray-100 rounded border flex items-center justify-center">
                          <span class="text-gray-500 text-xs">无图像</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-sm text-blue-600">未分割到指定对象</div>
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
                    {{ result.gemini_result?.error || '分割失败' }}
                  </div>
                </div>
              </div>

              <!-- OpenCV 结果 -->
              <div class="border border-green-200 rounded-lg p-4 bg-green-50">
                <div class="flex items-center justify-between mb-3">
                  <h4 class="font-medium text-green-800 flex items-center">
                    <i class="fas fa-eye mr-2"></i>
                    OpenCV 分割结果
                  </h4>
                  <span class="text-sm text-green-600">
                    {{ result.opencv_result?.success ? '成功' : '失败' }}
                  </span>
                </div>

                <div v-if="result.opencv_result?.success">
                  <div v-if="result.opencv_result.segmented_objects && result.opencv_result.segmented_objects.length > 0">
                    <p class="text-sm text-green-700 mb-3">分割到 {{ result.opencv_result.segmented_objects.length }} 个区域：</p>

                    <!-- 分割区域标签 -->
                    <div class="flex flex-wrap gap-1 mb-3">
                      <span v-for="obj in result.opencv_result.segmented_objects" :key="obj.label"
                            class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                        {{ obj.label }}
                        <span v-if="obj.confidence" class="ml-1 opacity-75">
                          ({{ Math.round(obj.confidence * 100) }}%)
                        </span>
                      </span>
                    </div>

                    <!-- 分割结果图像 -->
                    <div class="grid grid-cols-2 gap-2">
                      <div v-for="(obj, index) in result.opencv_result.segmented_objects" :key="index"
                           class="border rounded p-2 bg-white">
                        <div class="text-xs text-green-700 mb-1 font-medium">{{ obj.label }}</div>
                        <img v-if="obj.segment_image"
                             :src="getImageUrl(obj.segment_image)"
                             class="w-full h-24 object-contain rounded border"
                             :alt="obj.label"
                             @error="handleImageError">
                        <div v-else class="w-full h-24 bg-gray-100 rounded border flex items-center justify-center">
                          <span class="text-gray-500 text-xs">无图像</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-sm text-green-600">未分割到指定对象</div>
                </div>

                <div v-else class="p-3 bg-red-50 border border-red-200 rounded">
                  <div v-if="result.opencv_result?.message || result.opencv_result?.suggestion" class="text-sm">
                    <p v-if="result.opencv_result.message" class="text-red-700 mb-1 font-medium">{{ result.opencv_result.message }}</p>
                    <p v-if="result.opencv_result.suggestion" class="text-red-600 text-xs">{{ result.opencv_result.suggestion }}</p>
                    <div v-if="result.opencv_result.detected_objects && result.opencv_result.detected_objects.length > 0" class="mt-2">
                      <p class="text-red-600 text-xs mb-1">检测到的对象：</p>
                      <div class="flex flex-wrap gap-1">
                        <span v-for="obj in result.opencv_result.detected_objects.slice(0, 3)" :key="obj"
                              class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                          {{ obj }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-sm text-red-700">
                    {{ result.opencv_result?.error || '分割失败' }}
                  </div>
                </div>
              </div>

              <!-- YOLO 结果 -->
              <div class="border border-purple-200 rounded-lg p-4 bg-purple-50">
                <div class="flex items-center justify-between mb-3">
                  <h4 class="font-medium text-purple-800 flex items-center">
                    <i class="fas fa-search mr-2"></i>
                    YOLO 分割结果
                  </h4>
                  <span class="text-sm text-purple-600">
                    {{ result.yolo_result?.success ? '成功' : '失败' }}
                  </span>
                </div>

                <div v-if="result.yolo_result?.success">
                  <div v-if="result.yolo_result.segmented_objects && result.yolo_result.segmented_objects.length > 0">
                    <p class="text-sm text-purple-700 mb-3">分割到 {{ result.yolo_result.segmented_objects.length }} 个区域：</p>

                    <!-- 分割区域标签 -->
                    <div class="flex flex-wrap gap-1 mb-3">
                      <span v-for="obj in result.yolo_result.segmented_objects" :key="obj.label || obj.class_name"
                            class="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                        {{ obj.label || obj.class_name }}
                        <span v-if="obj.confidence" class="ml-1 opacity-75">
                          ({{ Math.round(obj.confidence * 100) }}%)
                        </span>
                      </span>
                    </div>

                    <!-- 分割结果图像 -->
                    <div class="grid grid-cols-2 gap-2">
                      <div v-for="(obj, index) in result.yolo_result.segmented_objects" :key="index"
                           class="border rounded p-2 bg-white">
                        <div class="text-xs text-purple-700 mb-1 font-medium">{{ obj.label || obj.class_name }}</div>
                        <img v-if="obj.segment_image || obj.image_path"
                             :src="getImageUrl(obj.segment_image || obj.image_path)"
                             class="w-full h-24 object-contain rounded border"
                             :alt="obj.label || obj.class_name"
                             @error="handleImageError">
                        <div v-else class="w-full h-24 bg-gray-100 rounded border flex items-center justify-center">
                          <span class="text-gray-500 text-xs">无图像</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-sm text-purple-600">未分割到指定对象</div>
                </div>

                <div v-else class="p-3 bg-red-50 border border-red-200 rounded">
                  <div v-if="result.yolo_result?.message || result.yolo_result?.suggestion" class="text-sm">
                    <p v-if="result.yolo_result.message" class="text-red-700 mb-1 font-medium">{{ result.yolo_result.message }}</p>
                    <p v-if="result.yolo_result.suggestion" class="text-red-600 text-xs">{{ result.yolo_result.suggestion }}</p>
                    <div v-if="result.yolo_result.alternative_queries && result.yolo_result.alternative_queries.length > 0" class="mt-2">
                      <p class="text-xs text-purple-600 mb-1">建议分割：</p>
                      <div class="flex flex-wrap gap-1">
                        <span v-for="query in result.yolo_result.alternative_queries.slice(0, 3)" :key="query"
                              class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded cursor-pointer hover:bg-blue-200"
                              @click="segmentationTarget = query">
                          {{ query }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-sm text-red-700">
                    {{ result.yolo_result?.error || '分割失败' }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 分割信息 -->
          <div class="text-sm text-gray-600 space-y-1">
            <p><strong>分割方法：</strong>{{ getMethodName(segmentationMethod) }}</p>
            <p v-if="result.processing_time"><strong>处理时间：</strong>{{ result.processing_time }}秒</p>
            <p v-if="segmentationTarget"><strong>分割目标：</strong>{{ segmentationTarget }}</p>
            <p v-if="result.total_segments"><strong>总分割数：</strong>{{ result.total_segments }}</p>
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
              <span class="bg-yellow-100 text-yellow-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">1</span>
              <p>上传需要分割的图像文件</p>
            </div>
            <div class="flex items-start">
              <span class="bg-yellow-100 text-yellow-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">2</span>
              <p>选择分割方法和算法参数</p>
            </div>
            <div class="flex items-start">
              <span class="bg-yellow-100 text-yellow-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">3</span>
              <p>可选择指定要分割的物体类型</p>
            </div>
            <div class="flex items-start">
              <span class="bg-yellow-100 text-yellow-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">4</span>
              <p>点击"开始分割"查看结果</p>
            </div>
          </div>

          <div class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div class="flex items-start">
              <i class="fas fa-lightbulb text-blue-600 mt-1 mr-3"></i>
              <div class="text-blue-800">
                <p class="font-medium mb-1">分割方法说明：</p>
                <ul class="text-sm space-y-1">
                  <li><strong>Gemini AI：</strong>使用Google AI进行智能图像分割</li>
                  <li><strong>OpenCV：</strong>传统计算机视觉分割算法</li>
                  <li><strong>YOLO：</strong>实时实例分割神经网络</li>
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
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/services/api'

export default {
  name: 'ImageSegmentation',
  setup() {
    const selectedFile = ref(null)
    const imagePreview = ref('')
    const segmentationMethod = ref('gemini')
    const segmentationTarget = ref('')
    const opencvAlgorithm = ref('watershed')
    const yoloModel = ref('yolo11n')
    const confidenceThreshold = ref(0.5)
    const loading = ref(false)
    const result = ref(null)
    const fileInput = ref(null)
    const availableYoloModels = ref({
      'yolo11n': { name: 'YOLOv11 Nano', description: '最快的模型，适合实时分割' },
      'yolo11s': { name: 'YOLOv11 Small', description: '平衡速度和精度' },
      'yolo11m': { name: 'YOLOv11 Medium', description: '中等精度，适合大多数场景' },
      'yolo11l': { name: 'YOLOv11 Large', description: '高精度模型' },
      'yolo11x': { name: 'YOLOv11 Extra Large', description: '最高精度，速度较慢' }
    })

    const handleFileUpload = (event) => {
      const file = event.target.files[0]
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

    const clearImage = () => {
      selectedFile.value = null
      imagePreview.value = ''
      result.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }

    const segmentImage = async () => {
      if (!selectedFile.value) {
        ElMessage.warning('请选择图像文件')
        return
      }

      loading.value = true
      result.value = null

      try {
        const formData = new FormData()
        formData.append('image', selectedFile.value)

        let endpoint = '/image-segmentation'

        if (segmentationMethod.value === 'opencv') {
          endpoint = '/image-segmentation/opencv'
          formData.append('method', opencvAlgorithm.value)
          formData.append('object_name', segmentationTarget.value)
        } else if (segmentationMethod.value === 'yolo') {
          endpoint = '/image-segmentation/yolo'
          formData.append('model_name', yoloModel.value)
          formData.append('confidence', confidenceThreshold.value)
          formData.append('user_query', segmentationTarget.value)
        } else if (segmentationMethod.value === 'comparison') {
          endpoint = '/image-segmentation/compare'
          formData.append('opencv_method', opencvAlgorithm.value)
          formData.append('yolo_model', yoloModel.value)
          formData.append('object_name', segmentationTarget.value)
        } else {
          // Gemini方法
          formData.append('object_name', segmentationTarget.value)
        }

        const response = await api.post(endpoint, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        if (response.data.success) {
          result.value = response.data
          ElMessage.success('分割完成！')
        } else {
          // 处理内容不匹配的情况
          if (response.data.explanation || response.data.suggestion || response.data.content_mismatch || response.data.message || response.data.detected_objects) {
            result.value = response.data
            ElMessage.warning(response.data.error || response.data.message || '分割失败')
          } else {
            throw new Error(response.data.error || '分割失败')
          }
        }
      } catch (error) {
        console.error('分割失败:', error)

        // 优先显示后端返回的友好错误信息
        let errorMessage = error.message || '分割失败，请重试'

        // 如果有建议信息，添加到错误消息中
        if (error.suggestion) {
          errorMessage += `\n建议：${error.suggestion}`
        }

        // 检查是否有特殊的分割结果数据（即使失败也可能有部分结果）
        if (error.backendError && (error.backendError.explanation || error.backendError.content_mismatch || error.backendError.detected_objects)) {
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

    return {
      selectedFile,
      imagePreview,
      segmentationMethod,
      segmentationTarget,
      opencvAlgorithm,
      yoloModel,
      confidenceThreshold,
      loading,
      result,
      fileInput,
      availableYoloModels,
      handleFileUpload,
      clearImage,
      segmentImage,
      getImageUrl,
      getMethodName,
      handleImageError
    }
  }
}
</script>

<style scoped>
/* 组件特定样式 */

/* 自定义滚动条样式 */
.scrollbar-thin {
  scrollbar-width: thin;
}

.scrollbar-thumb-gray-300::-webkit-scrollbar-thumb {
  background-color: #d1d5db;
  border-radius: 6px;
}

.scrollbar-track-gray-100::-webkit-scrollbar-track {
  background-color: #f3f4f6;
  border-radius: 6px;
}

.scrollbar-thin::-webkit-scrollbar {
  width: 8px;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: #d1d5db;
  border-radius: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background-color: #f3f4f6;
  border-radius: 6px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: #9ca3af;
}
</style>
