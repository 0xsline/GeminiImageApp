<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <!-- 页面标题 -->
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">图像编辑</h1>
      <p class="text-gray-600">使用AI技术和传统算法编辑和修改您的图像</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 左侧：上传和编辑选项 -->
      <div class="space-y-6">
        <!-- 图像上传 -->
        <div class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-upload text-xl text-blue-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">上传图像</h2>
          </div>

          <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
            <input type="file" @change="handleFileUpload" accept="image/*" class="hidden" ref="fileInput">
            <div v-if="!originalImage" @click="$refs.fileInput.click()" class="cursor-pointer">
              <i class="fas fa-cloud-upload-alt text-4xl text-gray-400 mb-4"></i>
              <p class="text-gray-600 mb-2">点击上传图像</p>
              <p class="text-sm text-gray-500">支持 JPG, PNG, GIF 格式</p>
            </div>
            <div v-else class="relative">
              <img :src="originalImage" class="max-w-full h-80 object-contain mx-auto rounded-lg">
              <button @click="clearImage" class="absolute top-2 right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm hover:bg-red-600">
                ×
              </button>
            </div>
          </div>
        </div>

        <!-- 编辑类型选择 -->
        <div v-if="originalImage" class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-edit text-xl text-green-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">编辑类型</h2>
          </div>

          <div class="grid grid-cols-1 gap-3">
            <button v-for="(editType, key) in editTypes" :key="key"
                    @click="selectedEditType = key"
                    :class="[
                      'p-4 border-2 rounded-lg text-left transition-colors',
                      selectedEditType === key
                        ? 'border-green-500 bg-green-50'
                        : 'border-gray-200 hover:border-green-300'
                    ]">
              <div class="flex items-center">
                <i :class="[editType.icon, 'text-xl mr-3']"
                   :style="{ color: selectedEditType === key ? '#10b981' : '#6b7280' }"></i>
                <div>
                  <h3 class="font-medium text-gray-900">{{ editType.name }}</h3>
                  <p class="text-sm text-gray-600">{{ editType.description }}</p>
                </div>
              </div>
            </button>
          </div>
        </div>

        <!-- 编辑参数 -->
        <div v-if="selectedEditType" class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-sliders-h text-xl text-purple-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">编辑参数</h2>
          </div>

          <!-- Gemini AI 编辑 -->
          <div v-if="selectedEditType === 'gemini'" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">编辑指令</label>
              <textarea v-model="editParams.instruction"
                        placeholder="请描述您想要对图像进行的编辑..."
                        class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                        rows="3"></textarea>
            </div>
          </div>

          <!-- 滤镜效果 -->
          <div v-else-if="selectedEditType === 'filter'" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">滤镜类型</label>
              <select v-model="editParams.filter_type" class="w-full p-3 border border-gray-300 rounded-lg">
                <option value="blur">模糊</option>
                <option value="sharpen">锐化</option>
                <option value="edge">边缘检测</option>
                <option value="emboss">浮雕</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">强度: {{ editParams.intensity }}</label>
              <input type="range" v-model="editParams.intensity" min="0.1" max="3.0" step="0.1" class="w-full">
            </div>
          </div>

          <!-- 图像增强 -->
          <div v-else-if="selectedEditType === 'enhance'" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">增强类型</label>
              <select v-model="editParams.enhance_type" class="w-full p-3 border border-gray-300 rounded-lg">
                <option value="brightness">亮度</option>
                <option value="contrast">对比度</option>
                <option value="saturation">饱和度</option>
                <option value="gamma">伽马校正</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">调整系数: {{ editParams.factor }}</label>
              <input type="range" v-model="editParams.factor" min="0.1" max="3.0" step="0.1" class="w-full">
            </div>
          </div>

          <!-- 图像变换 -->
          <div v-else-if="selectedEditType === 'transform'" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">变换类型</label>
              <select v-model="editParams.transform_type" class="w-full p-3 border border-gray-300 rounded-lg">
                <option value="resize">调整大小</option>
                <option value="rotate">旋转</option>
                <option value="flip">翻转</option>
                <option value="crop">裁剪</option>
              </select>
            </div>
            <div v-if="editParams.transform_type === 'resize'" class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">宽度</label>
                <input type="number" v-model="editParams.width" class="w-full p-3 border border-gray-300 rounded-lg">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">高度</label>
                <input type="number" v-model="editParams.height" class="w-full p-3 border border-gray-300 rounded-lg">
              </div>
            </div>
            <div v-if="editParams.transform_type === 'rotate'">
              <label class="block text-sm font-medium text-gray-700 mb-2">旋转角度: {{ editParams.angle }}°</label>
              <input type="range" v-model="editParams.angle" min="0" max="360" step="90" class="w-full">
            </div>
          </div>

          <!-- 图像修复 -->
          <div v-else-if="selectedEditType === 'repair'" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">修复类型</label>
              <select v-model="editParams.repair_type" class="w-full p-3 border border-gray-300 rounded-lg">
                <option value="denoise">去噪</option>
                <option value="blur_removal">去模糊</option>
                <option value="histogram_eq">直方图均衡化</option>
              </select>
            </div>
          </div>

          <button @click="applyEdit"
                  :disabled="loading"
                  class="w-full mt-6 bg-green-600 text-white py-3 px-6 rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
            <i v-if="loading" class="fas fa-spinner fa-spin mr-2"></i>
            {{ loading ? '处理中...' : '应用编辑' }}
          </button>
        </div>
      </div>

      <!-- 右侧：结果显示 -->
      <div class="space-y-6">
        <!-- 编辑结果 -->
        <div v-if="result" class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-check-circle text-xl text-green-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">编辑结果</h2>
          </div>

          <div class="space-y-4">
            <!-- 编辑结果图像 -->
            <div>
              <img :src="getImageUrl(getEditedImagePath(result))"
                   class="w-full h-96 object-contain rounded-lg shadow-md"
                   alt="编辑后的图像">
            </div>

            <!-- 编辑信息 -->
            <div class="text-sm text-gray-600 space-y-1">
              <p><strong>编辑类型：</strong>{{ editTypes[selectedEditType]?.name }}</p>
              <p v-if="result.edit_description"><strong>编辑描述：</strong>{{ result.edit_description }}</p>
              <p v-if="result.processing_time"><strong>处理时间：</strong>{{ result.processing_time }}秒</p>
            </div>
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
              <span class="bg-green-100 text-green-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">1</span>
              <p>上传您想要编辑的图像文件</p>
            </div>
            <div class="flex items-start">
              <span class="bg-green-100 text-green-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">2</span>
              <p>选择合适的编辑类型</p>
            </div>
            <div class="flex items-start">
              <span class="bg-green-100 text-green-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">3</span>
              <p>调整编辑参数</p>
            </div>
            <div class="flex items-start">
              <span class="bg-green-100 text-green-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">4</span>
              <p>点击"应用编辑"查看结果</p>
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
  name: 'ImageEditing',
  setup() {
    const originalImage = ref(null)
    const selectedEditType = ref(null)
    const loading = ref(false)
    const result = ref(null)
    const selectedFile = ref(null)
    const fileInput = ref(null)

    const editTypes = ref({
      gemini: {
        name: 'AI 智能编辑',
        description: 'Gemini AI',
        icon: 'fas fa-robot'
      },
      filter: {
        name: '滤镜效果',
        description: '图像滤镜',
        icon: 'fas fa-filter'
      },
      enhance: {
        name: '图像增强',
        description: '质量提升',
        icon: 'fas fa-adjust'
      },
      transform: {
        name: '图像变换',
        description: '几何变换',
        icon: 'fas fa-sync-alt'
      },
      repair: {
        name: '图像修复',
        description: '问题修复',
        icon: 'fas fa-tools'
      }
    })

    const editParams = ref({
      // Gemini AI 编辑
      instruction: '',
      gemini_model: 'gemini-2.0-flash-exp-image-generation',

      // 滤镜参数
      filter_type: 'blur',
      intensity: 1.0,

      // 增强参数
      enhance_type: 'brightness',
      factor: 1.2,

      // 变换参数
      transform_type: 'resize',
      width: 800,
      height: 600,
      angle: 90,

      // 修复参数
      repair_type: 'denoise',
      gamma: 1.2
    })

    const handleFileUpload = (event) => {
      const file = event.target.files[0]
      if (file) {
        selectedFile.value = file
        const reader = new FileReader()
        reader.onload = (e) => {
          originalImage.value = e.target.result
          result.value = null
        }
        reader.readAsDataURL(file)
      }
    }

    const clearImage = () => {
      selectedFile.value = null
      originalImage.value = null
      selectedEditType.value = null
      result.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }

    const applyEdit = async () => {
      if (!selectedFile.value || !selectedEditType.value) {
        ElMessage.warning('请选择图像和编辑类型')
        return
      }

      loading.value = true
      result.value = null

      try {
        const formData = new FormData()
        formData.append('image', selectedFile.value)
        formData.append('edit_type', selectedEditType.value)

        // 根据编辑类型添加相应的参数
        if (selectedEditType.value === 'gemini') {
          formData.append('instruction', editParams.value.instruction)
          formData.append('gemini_model', editParams.value.gemini_model)
        } else if (selectedEditType.value === 'filter') {
          formData.append('filter_type', editParams.value.filter_type)
          formData.append('intensity', editParams.value.intensity.toString())
        } else if (selectedEditType.value === 'enhance') {
          formData.append('enhance_type', editParams.value.enhance_type)
          formData.append('factor', editParams.value.factor.toString())
        } else if (selectedEditType.value === 'transform') {
          formData.append('transform_type', editParams.value.transform_type)
          if (editParams.value.transform_type === 'resize') {
            formData.append('width', editParams.value.width.toString())
            formData.append('height', editParams.value.height.toString())
          } else if (editParams.value.transform_type === 'rotate') {
            formData.append('angle', editParams.value.angle.toString())
          }
        } else if (selectedEditType.value === 'repair') {
          formData.append('repair_type', editParams.value.repair_type)
          if (editParams.value.repair_type === 'gamma_correction') {
            formData.append('gamma', editParams.value.gamma.toString())
          }
        }

        const response = await api.post('/image-editing', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        if (response.data.success) {
          result.value = response.data
          ElMessage.success('编辑完成！')
        } else {
          throw new Error(response.data.error || '编辑失败')
        }
      } catch (error) {
        console.error('编辑失败:', error)
        ElMessage.error(error.message || '编辑失败，请重试')
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

    const getEditedImagePath = (result) => {
      if (!result) return ''

      // 处理新的数据结构 (edited_images 数组)
      if (result.edited_images && result.edited_images.length > 0) {
        return result.edited_images[0]
      }

      // 处理旧的数据结构 (edited_image_path 字段)
      if (result.edited_image_path) {
        return result.edited_image_path
      }

      return ''
    }

    return {
      originalImage,
      selectedEditType,
      loading,
      result,
      selectedFile,
      editTypes,
      editParams,
      fileInput,
      handleFileUpload,
      clearImage,
      applyEdit,
      getImageUrl,
      getEditedImagePath
    }
  }
}
</script>

<style scoped>
/* 组件特定样式 */
</style>
