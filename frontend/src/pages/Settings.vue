<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- 页面标题 -->
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">设置</h1>
      <p class="text-gray-600">配置您的API密钥和应用偏好设置</p>
    </div>

    <!-- API配置 -->
    <div class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
      <div class="flex items-center mb-6">
        <i class="fas fa-key text-xl text-blue-500 mr-3"></i>
        <h2 class="text-xl font-semibold text-gray-900">API配置</h2>
      </div>

      <div class="space-y-4">
        <!-- Google AI API Key -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Google AI API Key
            <span class="text-red-500">*</span>
          </label>
          <div class="relative">
            <input
              v-model="apiKey"
              :type="showApiKey ? 'text' : 'password'"
              placeholder="请输入您的Google AI API Key"
              class="w-full p-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
            <button
              @click="showApiKey = !showApiKey"
              class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700">
              <i :class="showApiKey ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
            </button>
          </div>
          <p class="text-sm text-gray-600 mt-1">
            在 <a href="https://aistudio.google.com/app/apikey" target="_blank" class="text-blue-600 hover:underline">Google AI Studio</a> 获取您的API密钥
          </p>
        </div>

        <!-- API状态检测 -->
        <div class="flex items-center space-x-4">
          <button
            @click="testApiKey"
            :disabled="!apiKey || testing"
            class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
            <i v-if="testing" class="fas fa-spinner fa-spin mr-2"></i>
            {{ testing ? '测试中...' : '测试连接' }}
          </button>

          <div v-if="apiStatus" class="flex items-center">
            <i :class="apiStatus.success ? 'fas fa-check-circle text-green-500' : 'fas fa-times-circle text-red-500'" class="mr-2"></i>
            <span :class="apiStatus.success ? 'text-green-700' : 'text-red-700'">
              {{ apiStatus.message }}
            </span>
          </div>
        </div>

        <!-- 保存按钮 -->
        <button
          @click="saveApiKey"
          :disabled="!apiKey"
          class="w-full bg-green-600 text-white py-3 px-6 rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
          <i class="fas fa-save mr-2"></i>
          保存API密钥
        </button>
      </div>
    </div>

    <!-- 应用设置 -->
    <div class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
      <div class="flex items-center mb-6">
        <i class="fas fa-cog text-xl text-purple-500 mr-3"></i>
        <h2 class="text-xl font-semibold text-gray-900">应用设置</h2>
      </div>

      <div class="space-y-6">
        <!-- 主题设置 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-3">界面主题</label>
          <div class="grid grid-cols-2 gap-4">
            <button
              @click="setTheme('light')"
              :class="[
                'p-4 border-2 rounded-lg transition-colors',
                theme === 'light' ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:border-purple-300'
              ]">
              <div class="flex items-center">
                <i class="fas fa-sun text-yellow-500 text-xl mr-3"></i>
                <div class="text-left">
                  <h3 class="font-medium text-gray-900">浅色主题</h3>
                  <p class="text-sm text-gray-600">明亮清爽的界面</p>
                </div>
              </div>
            </button>

            <button
              @click="setTheme('dark')"
              :class="[
                'p-4 border-2 rounded-lg transition-colors',
                theme === 'dark' ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:border-purple-300'
              ]">
              <div class="flex items-center">
                <i class="fas fa-moon text-blue-500 text-xl mr-3"></i>
                <div class="text-left">
                  <h3 class="font-medium text-gray-900">深色主题</h3>
                  <p class="text-sm text-gray-600">护眼的深色界面</p>
                </div>
              </div>
            </button>
          </div>
        </div>

        <!-- 默认模型设置 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">默认AI模型</label>
          <select v-model="defaultModel" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
            <option value="gemini-2.0-flash">Gemini 2.0 Flash (推荐)</option>
            <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
            <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
          </select>
        </div>

        <!-- 自动保存设置 -->
        <div class="flex items-center justify-between">
          <div>
            <h3 class="font-medium text-gray-900">自动保存结果</h3>
            <p class="text-sm text-gray-600">自动保存生成的图像和视频到本地</p>
          </div>
          <button
            @click="autoSave = !autoSave"
            :class="[
              'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
              autoSave ? 'bg-purple-600' : 'bg-gray-200'
            ]">
            <span
              :class="[
                'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                autoSave ? 'translate-x-6' : 'translate-x-1'
              ]">
            </span>
          </button>
        </div>

        <!-- 保存设置按钮 -->
        <button
          @click="saveSettings"
          class="w-full bg-purple-600 text-white py-3 px-6 rounded-lg hover:bg-purple-700 transition-colors">
          <i class="fas fa-save mr-2"></i>
          保存设置
        </button>
      </div>
    </div>

    <!-- 关于信息 -->
    <div class="bg-white rounded-xl p-6 shadow-lg border border-gray-100">
      <div class="flex items-center mb-6">
        <i class="fas fa-info-circle text-xl text-green-500 mr-3"></i>
        <h2 class="text-xl font-semibold text-gray-900">关于应用</h2>
      </div>

      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span class="font-medium text-gray-700">应用版本：</span>
            <span class="text-gray-600">v1.0.0</span>
          </div>
          <div>
            <span class="font-medium text-gray-700">构建时间：</span>
            <span class="text-gray-600">{{ new Date().toLocaleDateString() }}</span>
          </div>
          <div>
            <span class="font-medium text-gray-700">技术栈：</span>
            <span class="text-gray-600">Vue 3 + Flask + Google AI</span>
          </div>
          <div>
            <span class="font-medium text-gray-700">开发者：</span>
            <span class="text-gray-600">Gemini Image App Team</span>
          </div>
        </div>

        <div class="pt-4 border-t border-gray-200">
          <p class="text-sm text-gray-600 leading-relaxed">
            Gemini图像处理平台是基于Google Gemini AI的强大图像处理应用，提供图像问答、生成、编辑、检测和分割等全方位服务。
            我们致力于为用户提供最先进的AI图像处理体验。
          </p>
        </div>

        <div class="flex space-x-4">
          <a href="https://github.com/0xsline" target="_blank" class="text-blue-600 hover:underline text-sm">
            <i class="fab fa-github mr-1"></i>
            GitHub
          </a>
          <a href="upunstop@example.com" class="text-blue-600 hover:underline text-sm">
            <i class="fas fa-envelope mr-1"></i>
            技术支持
          </a>
          <a href="https://github.com/0xsline/GeminiImageApp" class="text-blue-600 hover:underline text-sm">
            <i class="fas fa-book mr-1"></i>
            使用文档
          </a>
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
  name: 'Settings',
  setup() {
    const apiKey = ref('')
    const showApiKey = ref(false)
    const testing = ref(false)
    const apiStatus = ref(null)
    const theme = ref('light')
    const defaultModel = ref('gemini-2.0-flash')
    const autoSave = ref(true)

    // 加载设置
    const loadSettings = () => {
      const savedSettings = localStorage.getItem('gemini-app-settings')
      if (savedSettings) {
        const settings = JSON.parse(savedSettings)
        apiKey.value = settings.apiKey || ''
        theme.value = settings.theme || 'light'
        defaultModel.value = settings.defaultModel || 'gemini-2.0-flash'
        autoSave.value = settings.autoSave !== false
      }
    }

    // 测试API密钥
    const testApiKey = async () => {
      if (!apiKey.value) {
        ElMessage.warning('请输入API密钥')
        return
      }

      testing.value = true
      apiStatus.value = null

      try {
        const response = await api.post('/test-api-key', {
          api_key: apiKey.value
        })

        if (response.data.success) {
          apiStatus.value = {
            success: true,
            message: 'API密钥有效，连接成功！'
          }
          ElMessage.success('API密钥测试成功')
        } else {
          apiStatus.value = {
            success: false,
            message: response.data.error || 'API密钥无效'
          }
        }
      } catch (error) {
        // 优先显示后端返回的友好错误信息
        let errorMessage = error.message || '连接失败，请检查网络或API密钥'

        apiStatus.value = {
          success: false,
          message: errorMessage
        }

        console.error('API测试失败:', error)
      } finally {
        testing.value = false
      }
    }

    // 保存API密钥
    const saveApiKey = () => {
      if (!apiKey.value) {
        ElMessage.warning('请输入API密钥')
        return
      }

      const settings = JSON.parse(localStorage.getItem('gemini-app-settings') || '{}')
      settings.apiKey = apiKey.value
      localStorage.setItem('gemini-app-settings', JSON.stringify(settings))

      ElMessage.success('API密钥已保存')
    }

    // 设置主题
    const setTheme = (newTheme) => {
      theme.value = newTheme

      // 移除所有主题类
      document.documentElement.classList.remove('theme-light', 'theme-dark')
      document.body.classList.remove('theme-light', 'theme-dark')

      // 添加新主题类
      const themeClass = `theme-${newTheme}`
      document.documentElement.classList.add(themeClass)
      document.body.classList.add(themeClass)

      // 同时设置data-theme属性以备用
      document.documentElement.setAttribute('data-theme', newTheme)
    }

    // 保存设置
    const saveSettings = () => {
      const settings = {
        apiKey: apiKey.value,
        theme: theme.value,
        defaultModel: defaultModel.value,
        autoSave: autoSave.value
      }

      localStorage.setItem('gemini-app-settings', JSON.stringify(settings))
      setTheme(theme.value)

      ElMessage.success('设置已保存')
    }

    onMounted(() => {
      loadSettings()
      setTheme(theme.value)
    })

    return {
      apiKey,
      showApiKey,
      testing,
      apiStatus,
      theme,
      defaultModel,
      autoSave,
      testApiKey,
      saveApiKey,
      setTheme,
      saveSettings
    }
  }
}
</script>

<style scoped>
/* 组件特定样式 */
</style>
