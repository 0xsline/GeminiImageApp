<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <!-- 页面标题 -->
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">视频生成</h1>
      <p class="text-gray-600">使用AI技术生成高质量视频内容 - 支持本地文件处理</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 左侧：输入和设置 -->
      <div class="space-y-6">
        <!-- 生成模式选择 -->
        <div class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-magic text-xl text-purple-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">生成模式</h2>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <button @click="generationMode = 'text'"
                    :class="['p-4 rounded-lg border-2 transition-all text-left',
                             generationMode === 'text' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-indigo-300']">
              <div class="flex items-center mb-2">
                <i class="fas fa-keyboard text-indigo-500 mr-2"></i>
                <span class="font-medium">文本生成视频</span>
              </div>
              <p class="text-sm text-gray-600">通过文字描述生成视频</p>
            </button>

            <button @click="generationMode = 'image'"
                    :class="['p-4 rounded-lg border-2 transition-all text-left',
                             generationMode === 'image' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-indigo-300']">
              <div class="flex items-center mb-2">
                <i class="fas fa-image text-indigo-500 mr-2"></i>
                <span class="font-medium">图像生成视频</span>
              </div>
              <p class="text-sm text-gray-600">基于本地图像文件生成视频</p>
            </button>
          </div>
        </div>

        <!-- 图像选择（仅在图像模式下显示） -->
        <div v-if="generationMode === 'image'" class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-image text-xl text-indigo-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">选择参考图像</h2>
          </div>

          <!-- 图像上传说明 -->
          <div class="mb-6">
            <p class="text-sm text-gray-600">
              <i class="fas fa-info-circle mr-2"></i>
              请上传一张图像作为视频生成的参考
            </p>
          </div>

          <!-- 上传图像 -->
          <div class="space-y-4">
            <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-indigo-400 transition-colors">
              <input type="file" @change="handleImageUpload" accept="image/*" class="hidden" ref="imageFileInput">
              <div v-if="!uploadedImagePreview" @click="$refs.imageFileInput.click()" class="cursor-pointer">
                <i class="fas fa-cloud-upload-alt text-4xl text-gray-400 mb-4"></i>
                <p class="text-gray-600 mb-2">点击上传图像</p>
                <p class="text-sm text-gray-500">支持 JPG, PNG, GIF 格式</p>
              </div>
              <div v-else class="relative">
                <img :src="uploadedImagePreview" class="max-w-full h-64 object-contain mx-auto rounded-lg">
                <button @click="clearUploadedImage" class="absolute top-2 right-2 bg-red-500 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm hover:bg-red-600">
                  ×
                </button>
              </div>
            </div>
            <p v-if="uploadedImageFile" class="text-sm text-gray-600">
              <i class="fas fa-check-circle text-green-500 mr-1"></i>
              已选择: {{ uploadedImageFile.name }}
            </p>
          </div>
        </div>

        <!-- 描述输入卡片 -->
        <div class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-video text-xl text-indigo-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">
              {{ generationMode === 'image' ? '视频动画描述' : '视频描述' }}
            </h2>
          </div>

          <textarea v-model="prompt"
                    :placeholder="generationMode === 'image' ? '描述希望图像如何动起来（可选，AI会自动优化）...' : '请输入您想要生成的视频描述...'"
                    class="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                    rows="4"></textarea>

          <!-- 示例提示词 -->
          <div class="mt-4">
            <p class="text-sm text-gray-600 mb-2">示例提示词：</p>
            <div class="grid grid-cols-1 gap-2">
              <button v-for="example in currentExamples" :key="example"
                      @click="prompt = example"
                      class="text-left px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-indigo-100 hover:text-indigo-700 transition-colors">
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
            <!-- 视频时长 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">视频时长</label>
              <select v-model="duration" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
                <option value="5">5秒 - 快速展示</option>
                <option value="6">6秒 - 标准短视频</option>
                <option value="7">7秒 - 详细展示</option>
                <option value="8">8秒 - 完整叙述</option>
              </select>
            </div>

            <!-- 宽高比 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">宽高比</label>
              <select v-model="aspectRatio" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
                <option value="16:9">横屏 (16:9) - 适合电脑观看</option>
                <option value="9:16">竖屏 (9:16) - 适合手机观看</option>
              </select>
            </div>

            <!-- 视频风格 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">视频风格</label>
              <select v-model="style" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
                <option value="realistic">写实风格</option>
                <option value="cinematic">电影风格</option>
                <option value="animation">动画风格</option>
                <option value="artistic">艺术风格</option>
                <option value="vintage">复古风格</option>
                <option value="futuristic">未来风格</option>
              </select>
            </div>

            <!-- 负面提示词 -->
            <div v-if="generationMode === 'text'">
              <label class="block text-sm font-medium text-gray-700 mb-2">负面提示词 (可选)</label>
              <input v-model="negativePrompt"
                     type="text"
                     placeholder="描述不希望出现的内容，如：模糊、低质量、扭曲等"
                     class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
            </div>
          </div>

          <button @click="generateVideo"
                  :disabled="loading || !canGenerate"
                  class="w-full mt-6 bg-indigo-600 text-white py-3 px-6 rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
            <i v-if="loading" class="fas fa-spinner fa-spin mr-2"></i>
            {{ loading ? '生成中...' : (generationMode === 'image' ? '生成动画视频' : '生成视频') }}
          </button>
        </div>
      </div>

      <!-- 右侧：结果显示 -->
      <div class="space-y-6">
        <!-- 生成进度 -->
        <div v-if="loading" class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-clock text-xl text-orange-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">生成进度</h2>
          </div>

          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600">{{ progressStatus }}</span>
              <span class="text-sm text-gray-600">{{ progressPercent }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                   :style="{ width: progressPercent + '%' }"></div>
            </div>
            <p class="text-sm text-gray-600">预计剩余时间: {{ estimatedTime }}</p>
          </div>
        </div>

        <!-- 生成结果 -->
        <div v-if="result" class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
          <div class="flex items-center mb-4">
            <i class="fas fa-play-circle text-xl text-green-500 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900">生成结果</h2>
          </div>

          <!-- 视频播放器 -->
          <div v-if="result.video_path" class="mb-4">
            <video :src="getVideoUrl(result.video_path)"
                   controls
                   class="w-full rounded-lg shadow-md"
                   :poster="result.thumbnail_path ? getVideoUrl(result.thumbnail_path) : ''">
              您的浏览器不支持视频播放。
            </video>
          </div>

          <!-- 视频信息 -->
          <div class="text-sm text-gray-600 space-y-1">
            <p><strong>原始提示词：</strong>{{ result.original_prompt }}</p>
            <p v-if="result.optimized_prompt"><strong>优化提示词：</strong>{{ result.optimized_prompt }}</p>
            <p><strong>视频时长：</strong>{{ result.duration }}秒</p>
            <p><strong>宽高比：</strong>{{ result.aspect_ratio }}</p>
            <p><strong>视频风格：</strong>{{ result.style }}</p>
            <p v-if="result.file_size"><strong>文件大小：</strong>{{ result.file_size }}</p>
            <p v-if="result.generation_time"><strong>生成时间：</strong>{{ result.generation_time }}</p>
            <p><strong>模型：</strong>{{ result.model || 'Veo 2.0' }}</p>
          </div>

          <!-- 下载按钮 -->
          <div class="mt-4 flex space-x-2">
            <a v-if="result.video_path"
               :href="getVideoUrl(result.video_path)"
               download
               class="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors text-center">
              <i class="fas fa-download mr-2"></i>
              下载视频
            </a>
            <button @click="shareVideo"
                    class="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
              <i class="fas fa-share mr-2"></i>
              分享视频
            </button>
          </div>
        </div>

        <!-- 使用说明 -->
        <div v-if="!result && !loading" class="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-100 dark:border-gray-700">
          <div class="flex items-center mb-4">
            <i class="fas fa-info-circle text-xl text-blue-500 dark:text-blue-400 mr-3"></i>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">使用说明</h2>
          </div>
          <div class="space-y-3 text-gray-600 dark:text-gray-300">
            <div class="flex items-start">
              <span class="bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">1</span>
              <p>输入详细的视频场景描述</p>
            </div>
            <div class="flex items-start">
              <span class="bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">2</span>
              <p>选择视频时长、质量和风格</p>
            </div>
            <div class="flex items-start">
              <span class="bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">3</span>
              <p>点击"生成视频"开始创作</p>
            </div>
            <div class="flex items-start">
              <span class="bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 rounded-full w-6 h-6 flex items-center justify-center text-sm font-medium mr-3 mt-0.5">4</span>
              <p>等待AI生成高质量视频</p>
            </div>
          </div>

          <div class="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg">
            <div class="flex items-start">
              <i class="fas fa-lightbulb text-yellow-600 dark:text-yellow-400 mt-1 mr-3"></i>
              <div class="text-yellow-800 dark:text-yellow-200">
                <p class="font-medium mb-1">提示词建议：</p>
                <p class="text-sm">描述具体的场景、动作、光线和氛围。包含摄像机运动、角度变化等细节可以获得更好的效果。</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/services/api'

export default {
  name: 'VideoGeneration',
  setup() {
    const prompt = ref('')
    const duration = ref('8')
    const aspectRatio = ref('16:9')
    const style = ref('realistic')
    const negativePrompt = ref('')
    const loading = ref(false)
    const result = ref(null)
    const progressPercent = ref(0)
    const progressStatus = ref('')
    const estimatedTime = ref('')
    const generationMode = ref('text')
    const uploadedImageFile = ref(null)
    const uploadedImagePreview = ref('')

    // 文本生成示例提示词
    const textExamples = ref([
      '黎明时分的未来城市全景。飞行器在摩天大楼间穿梭。镜头随着日出缓缓横移过天际线。',
      '一颗完美成熟的苹果挂在枝头，表面覆盖着露珠。微风轻拂，苹果缓缓旋转。',
      '博物馆展示柜中，戴着手套的小偷伸手去拿无价的钻石项链。镜头缓慢跟踪手部动作。',
      '一个巨大友善的机器人漫步在野花丛中，蝴蝶在它头部周围飞舞。镜头向上倾斜。',
      '夜晚霓虹灯照亮的城市街道，一辆复古汽车驶过，雨水反射着彩色灯光。',
      '蜘蛛网上的露珠微距镜头，晨光创造出彩虹般的反射效果。',
      '海浪拍打岩石悬崖的航拍镜头，海鸥在头顶慢动作翱翔。'
    ])

    // 图像动画示例提示词
    const imageExamples = ref([
      '轻柔的镜头推进，带有微妙的视差效果，柔和的自然光线',
      '慢动作效果，空中飘浮的粒子，电影级景深',
      '动态镜头运动，流畅过渡，温暖的黄金时光照明',
      '延时摄影效果，背景云朵移动，鲜艳色彩',
      '微妙的动画效果，自然风吹效果，梦幻氛围',
      '跟踪镜头，背景虚化效果，专业电影摄影',
      '自然运动，环境细节栩栩如生'
    ])

    // 当前示例提示词（根据模式切换）
    const currentExamples = computed(() => {
      return generationMode.value === 'image' ? imageExamples.value : textExamples.value
    })

    // 检查是否可以生成视频
    const canGenerate = computed(() => {
      if (generationMode.value === 'text') {
        return prompt.value.trim().length > 0
      } else {
        return uploadedImageFile.value !== null
      }
    })

    // 处理图像上传
    const handleImageUpload = (event) => {
      const file = event.target.files[0]
      if (file) {
        uploadedImageFile.value = file
        const reader = new FileReader()
        reader.onload = (e) => {
          uploadedImagePreview.value = e.target.result
        }
        reader.readAsDataURL(file)
      }
    }

    // 清除上传的图像
    const clearUploadedImage = () => {
      uploadedImageFile.value = null
      uploadedImagePreview.value = ''
      if (document.querySelector('input[type="file"]')) {
        document.querySelector('input[type="file"]').value = ''
      }
    }



    // 生成视频
    const generateVideo = async () => {
      // 验证输入
      if (generationMode.value === 'text' && !prompt.value.trim()) {
        ElMessage.warning('请输入视频描述')
        return
      }

      if (generationMode.value === 'image' && !uploadedImageFile.value) {
        ElMessage.warning('请上传一张图像')
        return
      }

      loading.value = true
      result.value = null
      progressPercent.value = 0
      progressStatus.value = '开始生成...'
      estimatedTime.value = '计算中...'

      // 模拟进度更新
      const progressInterval = setInterval(() => {
        if (progressPercent.value < 90) {
          progressPercent.value += Math.random() * 10
          if (progressPercent.value < 30) {
            progressStatus.value = generationMode.value === 'image' ? '处理图像...' : '分析提示词...'
            estimatedTime.value = '约2分钟'
          } else if (progressPercent.value < 60) {
            progressStatus.value = '生成视频帧...'
            estimatedTime.value = '约1分钟'
          } else {
            progressStatus.value = '合成视频...'
            estimatedTime.value = '约30秒'
          }
        }
      }, 1000)

      try {
        let response

        if (generationMode.value === 'text') {
          // 文本生成视频
          response = await api.post('/video-generation', {
            prompt: prompt.value,
            duration: parseInt(duration.value),
            aspect_ratio: aspectRatio.value,
            style: style.value,
            negative_prompt: negativePrompt.value.trim() || undefined
          })
        } else {
          // 上传图像生成视频
          const formData = new FormData()
          formData.append('image', uploadedImageFile.value)
          formData.append('prompt', prompt.value || '')
          formData.append('duration', duration.value)
          formData.append('aspect_ratio', aspectRatio.value)

          response = await api.post('/video-generation/from-image', formData)
        }

        clearInterval(progressInterval)
        progressPercent.value = 100
        progressStatus.value = '生成完成！'

        if (response.data.success) {
          result.value = response.data
          ElMessage.success(
            generationMode.value === 'image'
              ? '基于本地图像的视频生成成功！'
              : '视频生成成功！'
          )
        } else {
          throw new Error(response.data.error || '生成失败')
        }
      } catch (error) {
        clearInterval(progressInterval)
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

    const getVideoUrl = (videoPath) => {
      return videoPath ? `/${videoPath}` : ''
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const shareVideo = () => {
      if (navigator.share && result.value?.video_path) {
        navigator.share({
          title: '我生成的AI视频',
          text: result.value.original_prompt || '基于本地图像生成的视频',
          url: window.location.href
        })
      } else {
        // 复制链接到剪贴板
        navigator.clipboard.writeText(window.location.href)
        ElMessage.success('链接已复制到剪贴板')
      }
    }



    return {
      prompt,
      duration,
      aspectRatio,
      style,
      negativePrompt,
      loading,
      result,
      progressPercent,
      progressStatus,
      estimatedTime,
      generationMode,
      uploadedImageFile,
      uploadedImagePreview,
      textExamples,
      imageExamples,
      currentExamples,
      canGenerate,
      generateVideo,
      getVideoUrl,
      formatFileSize,
      shareVideo,
      handleImageUpload,
      clearUploadedImage
    }
  }
}
</script>

<style scoped>
/* 组件特定样式 */
.video-container {
  position: relative;
  overflow: hidden;
  border-radius: 8px;
}

.image-selector {
  transition: all 0.2s ease;
}

.image-selector:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.generation-mode-button {
  transition: all 0.3s ease;
}

.generation-mode-button:hover {
  transform: translateY(-1px);
}
</style>
