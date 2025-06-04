<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <!-- 页面标题 -->
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">图像生成</h1>
      <p class="text-gray-600">使用中文描述创建精美图像，支持多种AI模型</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 左侧：输入和设置 -->
      <div class="space-y-6">
        <!-- 描述输入卡片 -->
        <div class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-magic text-xl text-purple-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">描述文本</h2>
          </div>

          <textarea v-model="prompt"
                    placeholder="请输入您想要生成的图像描述..."
                    class="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none overflow-y-auto"
                    rows="4"
                    style="max-height: 120px;"></textarea>

          <!-- 示例提示词 -->
          <div class="mt-4">
            <p class="text-sm text-gray-600 mb-2">示例提示词：</p>
            <div class="grid grid-cols-1 gap-2">
              <button v-for="example in examplePrompts" :key="example"
                      @click="prompt = example"
                      class="text-left px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-purple-100 hover:text-purple-700 transition-colors">
                {{ example }}
              </button>
            </div>
          </div>
        </div>

        <!-- 生成设置 -->
        <div class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-cog text-xl text-blue-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">生成设置</h2>
          </div>

          <div class="space-y-4">
            <!-- 模型选择 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">AI模型</label>
              <select v-model="model" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
                <option v-for="(modelInfo, key) in availableModels" :key="key" :value="key">
                  {{ modelInfo.name }}
                </option>
              </select>
              <p v-if="availableModels[model]" class="text-sm text-gray-600 mt-1">
                {{ availableModels[model].description }}
              </p>
            </div>

            <!-- 宽高比 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">宽高比</label>
              <select v-model="aspectRatio" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
                <option v-for="(ratioInfo, key) in availableRatios" :key="key" :value="key">
                  {{ ratioInfo.name }}
                </option>
              </select>
            </div>

            <!-- 风格选择 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">图像风格</label>
              <select v-model="style" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
                <option v-for="(styleInfo, key) in availableStyles" :key="key" :value="key">
                  {{ styleInfo.name }}
                </option>
              </select>
              <p v-if="availableStyles[style]" class="text-sm text-gray-600 mt-1">
                {{ availableStyles[style].description }}
              </p>
            </div>
          </div>

          <button @click="generateImage"
                  :disabled="loading || !prompt.trim()"
                  class="w-full mt-6 bg-purple-600 text-white py-3 px-6 rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
            <i v-if="loading" class="fas fa-spinner fa-spin mr-2"></i>
            {{ loading ? '生成中...' : '生成图像' }}
          </button>
        </div>
      </div>

      <!-- 右侧：结果显示 -->
      <div class="space-y-6">
        <!-- 生成结果 -->
        <div v-if="result" class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-image text-xl text-green-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">生成结果</h2>
          </div>

          <!-- 生成的图像 -->
          <div v-if="result.images && result.images.length > 0" class="space-y-4">
            <div v-for="(image, index) in result.images" :key="index" class="relative">
              <img :src="getImageUrl(image.path)"
                   class="w-full rounded-lg shadow-md"
                   :alt="`生成的图像 ${index + 1}`">
              <div class="absolute top-2 right-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-sm">
                {{ index + 1 }}/{{ result.images.length }}
              </div>
            </div>
          </div>

          <!-- 创作方案（当API不可用时） -->
          <div v-else-if="result.creation_plan" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div class="flex items-start">
              <i class="fas fa-lightbulb text-blue-500 mt-1 mr-3"></i>
              <div class="flex-1">
                <h3 class="font-medium text-blue-800 mb-2">创作方案</h3>
                <div class="text-blue-700 whitespace-pre-line">{{ result.creation_plan }}</div>
              </div>
            </div>
          </div>

          <!-- 生成信息 -->
          <div class="mt-4 text-sm text-gray-600 space-y-1">
            <p><strong>原始提示词：</strong></p>
            <div class="bg-gray-50 p-3 rounded-lg max-h-20 overflow-y-auto text-gray-700 text-sm">
              {{ result.original_prompt }}
            </div>
            <div v-if="result.optimized_prompt">
              <p><strong>优化提示词：</strong></p>
              <div class="bg-blue-50 p-3 rounded-lg max-h-24 overflow-y-auto text-gray-700 text-sm">
                {{ result.optimized_prompt }}
              </div>
            </div>
            <p><strong>使用模型：</strong>{{ result.model }}</p>
            <p><strong>宽高比：</strong>{{ result.aspect_ratio }}</p>
            <p><strong>风格：</strong>{{ result.style }}</p>
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
              <span class="bg-purple-100 text-purple-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">1</span>
              <p>输入详细的图像描述文本</p>
            </div>
            <div class="flex items-start">
              <span class="bg-purple-100 text-purple-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">2</span>
              <p>选择合适的AI模型和生成参数</p>
            </div>
            <div class="flex items-start">
              <span class="bg-purple-100 text-purple-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">3</span>
              <p>点击"生成图像"开始创作</p>
            </div>
            <div class="flex items-start">
              <span class="bg-purple-100 text-purple-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">4</span>
              <p>等待AI生成高质量图像</p>
            </div>
          </div>

          <div class="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div class="flex items-start">
              <i class="fas fa-lightbulb text-yellow-600 mt-1 mr-3"></i>
              <div class="text-yellow-800">
                <p class="font-medium mb-1">提示词建议：</p>
                <p class="text-sm">使用具体、详细的描述可以获得更好的生成效果。包含风格、颜色、构图等细节信息。</p>
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

export default {
  name: 'ImageGeneration',
  setup() {
    const prompt = ref('')
    const model = ref('imagen-3.0-generate-002')
    const aspectRatio = ref('1:1')
    const style = ref('realistic')
    const loading = ref(false)
    const result = ref(null)
    const availableModels = ref({})
    const availableStyles = ref({})
    const availableRatios = ref({})

    const examplePrompts = ref([
      '一只可爱的小猫坐在花园里',
      '未来城市的天际线，霓虹灯闪烁',
      '宁静的山湖景色，倒影清晰',
      '抽象艺术风格的彩色漩涡',
      '古老的城堡在月光下',
      '热带海滩的日落景色',
      '科幻风格的机器人',
      '梦幻般的森林仙境'
    ])

    // 加载生成选项
    const loadGenerationOptions = async () => {
      try {
        const response = await api.get('/image-generation/options')
        if (response.data.success) {
          availableModels.value = response.data.models
          availableStyles.value = response.data.styles
          availableRatios.value = response.data.aspect_ratios
          model.value = response.data.default_model
          style.value = response.data.default_style
          aspectRatio.value = response.data.default_aspect_ratio
        }
      } catch (error) {
        console.error('加载生成选项失败:', error)
        // 静默处理，不显示错误消息，因为这不是用户主动操作
      }
    }

    const generateImage = async () => {
      if (!prompt.value.trim()) {
        ElMessage.warning('请输入描述文本')
        return
      }

      loading.value = true
      result.value = null

      try {
        const response = await api.post('/image-generation', {
          prompt: prompt.value,
          model: model.value,
          aspect_ratio: aspectRatio.value,
          style: style.value
        })

        if (response.data.success) {
          result.value = response.data
          ElMessage.success('图像生成成功！')
        } else {
          throw new Error(response.data.error || '生成失败')
        }
      } catch (error) {
        console.error('生成失败:', error)

        // 优先显示后端返回的友好错误信息
        let errorMessage = error.message || '生成失败，请重试'

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

    onMounted(() => {
      loadGenerationOptions()
    })

    return {
      prompt,
      model,
      aspectRatio,
      style,
      loading,
      result,
      availableModels,
      availableStyles,
      availableRatios,
      examplePrompts,
      generateImage,
      getImageUrl
    }
  }
}
</script>

<style scoped>
/* 组件特定样式 */
</style>
