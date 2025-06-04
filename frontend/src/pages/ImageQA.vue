<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <!-- 页面标题 -->
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">图像问答</h1>
      <p class="text-gray-600">上传图像并提问，获得AI驱动的详细中文回答</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 左侧：上传和提问 -->
      <div class="space-y-6">
        <!-- 图像上传卡片 -->
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

        <!-- 模型选择 -->
        <div class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-cog text-xl text-green-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">模型选择</h2>
          </div>
          <select v-model="selectedModel" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
            <option v-for="(model, key) in availableModels" :key="key" :value="key">
              {{ model.name }} {{ model.recommended ? '(推荐)' : '' }}
            </option>
          </select>
          <p v-if="availableModels[selectedModel]" class="text-sm text-gray-600 mt-2">
            {{ availableModels[selectedModel].description }}
          </p>
        </div>

        <!-- 问题输入 -->
        <div class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-question-circle text-xl text-purple-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">提出问题</h2>
          </div>

          <textarea v-model="question"
                    placeholder="请输入您想了解的关于图像的问题..."
                    class="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    rows="4"></textarea>

          <!-- 示例问题 -->
          <div class="mt-4">
            <p class="text-sm text-gray-600 mb-2">示例问题：</p>
            <div class="flex flex-wrap gap-2">
              <button v-for="example in exampleQuestions" :key="example"
                      @click="question = example"
                      class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-blue-100 hover:text-blue-700 transition-colors">
                {{ example }}
              </button>
            </div>
          </div>

          <button @click="submitQuestion"
                  :disabled="loading || !selectedFile || !question.trim()"
                  class="w-full mt-4 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
            <i v-if="loading" class="fas fa-spinner fa-spin mr-2"></i>
            {{ loading ? '分析中...' : '开始分析' }}
          </button>
        </div>
      </div>

      <!-- 右侧：结果显示 -->
      <div class="space-y-6">
        <!-- AI回答 -->
        <div v-if="result" class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-robot text-xl text-purple-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">AI 回答</h2>
          </div>

          <div class="mb-4">
            <img :src="imagePreview"
                 class="w-full h-64 object-contain rounded-lg shadow-md"
                 alt="分析的图像">
          </div>

          <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
            <div class="flex items-start">
              <i class="fas fa-check-circle text-green-500 mt-1 mr-3"></i>
              <div class="flex-1">
                <p class="text-green-800 leading-relaxed">{{ result.answer }}</p>
              </div>
            </div>
          </div>

          <div class="text-sm text-gray-600 space-y-1">
            <p><strong>问题：</strong>{{ result.question }}</p>
            <p><strong>使用模型：</strong>{{ result.model_used }}</p>
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
              <span class="bg-blue-100 text-blue-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">1</span>
              <p>上传您想要分析的图像文件</p>
            </div>
            <div class="flex items-start">
              <span class="bg-blue-100 text-blue-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">2</span>
              <p>选择合适的AI模型（推荐使用默认模型）</p>
            </div>
            <div class="flex items-start">
              <span class="bg-blue-100 text-blue-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">3</span>
              <p>输入您想了解的关于图像的问题</p>
            </div>
            <div class="flex items-start">
              <span class="bg-blue-100 text-blue-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">4</span>
              <p>点击"开始分析"获得AI的详细回答</p>
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

export default {
  name: 'ImageQA',
  setup() {
    const selectedFile = ref(null)
    const imagePreview = ref('')
    const question = ref('')
    const loading = ref(false)
    const result = ref(null)
    const selectedModel = ref('gemini-2.0-flash')
    const availableModels = ref({})
    const fileInput = ref(null)

    const exampleQuestions = ref([
      '这张图像中有什么物体？',
      '描述这张图像的颜色和情绪。',
      '这张图像的主要主题是什么？',
      '你能数一下这张图像中有多少人吗？',
      '这张图像是在什么环境中拍摄的？',
      '图像中的文字内容是什么？'
    ])

    // 加载可用模型
    const loadAvailableModels = async () => {
      try {
        const response = await api.get('/image-qa/models')
        if (response.data.success) {
          availableModels.value = response.data.models
          selectedModel.value = response.data.default_model
        }
      } catch (error) {
        console.error('加载模型失败:', error)
        // 静默处理，不显示错误消息，因为这不是用户主动操作
      }
    }

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

    const submitQuestion = async () => {
      if (!selectedFile.value || !question.value.trim()) {
        ElMessage.warning('请选择图像并输入问题')
        return
      }

      loading.value = true
      result.value = null

      try {
        const formData = new FormData()
        formData.append('image', selectedFile.value)
        formData.append('question', question.value)
        formData.append('model', selectedModel.value)

        const response = await api.post('/image-qa', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        if (response.data.success) {
          result.value = response.data
          ElMessage.success('分析完成！')
        } else {
          throw new Error(response.data.error || '处理失败')
        }
      } catch (error) {
        console.error('处理失败:', error)

        // 优先显示后端返回的友好错误信息
        let errorMessage = error.message || '处理失败，请重试'

        // 如果有建议信息，添加到错误消息中
        if (error.suggestion) {
          errorMessage += `\n建议：${error.suggestion}`
        }

        ElMessage.error(errorMessage)
      } finally {
        loading.value = false
      }
    }

    const getImageUrl = (imagePath) => {
      return imagePath ? `/${imagePath}` : ''
    }

    onMounted(() => {
      loadAvailableModels()
    })

    return {
      selectedFile,
      imagePreview,
      question,
      loading,
      result,
      selectedModel,
      availableModels,
      exampleQuestions,
      fileInput,
      handleFileUpload,
      clearImage,
      submitQuestion,
      getImageUrl
    }
  }
}
</script>

<style scoped>
/* 组件特定样式 */
</style>
