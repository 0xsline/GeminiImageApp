/**
 * API服务模块
 * 处理与后端API的通信
 */

// 创建axios风格的API响应对象
const createResponse = (data) => ({
  data,
  status: 200,
  statusText: 'OK'
})

class ApiService {
  constructor() {
    this.baseURL = '/api'
    this.timeout = 30000 // 30秒超时
  }

  /**
   * 获取用户保存的API密钥
   */
  getUserApiKey() {
    try {
      const settings = localStorage.getItem('gemini-app-settings')
      if (settings) {
        const parsed = JSON.parse(settings)
        return parsed.apiKey || null
      }
    } catch (error) {
      console.warn('获取API密钥失败:', error)
    }
    return null
  }

  /**
   * 发送HTTP请求的通用方法
   */
  async request(url, options = {}) {
    const config = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: this.timeout,
      ...options
    }

    // 如果是FormData，移除Content-Type让浏览器自动设置
    if (config.body instanceof FormData) {
      delete config.headers['Content-Type']
    }

    // 添加用户API密钥到请求头
    const userApiKey = this.getUserApiKey()
    if (userApiKey) {
      config.headers['X-API-Key'] = userApiKey
    }

    try {
      const response = await fetch(`${this.baseURL}${url}`, config)

      const contentType = response.headers.get('content-type')
      let data
      if (contentType && contentType.includes('application/json')) {
        data = await response.json()
      } else {
        data = await response.text()
      }

      if (!response.ok) {
        // 创建包含详细错误信息的错误对象
        const error = new Error()

        if (typeof data === 'object' && data.error) {
          // 后端返回了友好的错误信息
          error.message = data.error
          error.suggestion = data.suggestion
          error.errorType = data.error_type
          error.statusCode = response.status
          error.backendError = data
        } else {
          // 使用默认的HTTP错误信息
          error.message = `HTTP ${response.status}: ${response.statusText}`
          error.statusCode = response.status
        }

        throw error
      }

      // 返回axios风格的响应对象
      return createResponse(data)
    } catch (error) {
      console.error('API请求失败:', error)
      throw error
    }
  }

  /**
   * GET请求
   */
  async get(url, params = {}) {
    const queryString = new URLSearchParams(params).toString()
    const fullUrl = queryString ? `${url}?${queryString}` : url
    return this.request(fullUrl)
  }

  /**
   * POST请求
   */
  async post(url, data = {}, options = {}) {
    return this.request(url, {
      method: 'POST',
      body: data instanceof FormData ? data : JSON.stringify(data),
      ...options
    })
  }

  /**
   * PUT请求
   */
  async put(url, data = {}) {
    return this.request(url, {
      method: 'PUT',
      body: data instanceof FormData ? data : JSON.stringify(data)
    })
  }

  /**
   * DELETE请求
   */
  async delete(url) {
    return this.request(url, {
      method: 'DELETE'
    })
  }

  // 图像问答相关API
  async imageQA(formData) {
    return this.post('/image-qa', formData)
  }

  async getImageQAModels() {
    return this.get('/image-qa/models')
  }

  // 图像生成相关API
  async generateImage(data) {
    return this.post('/image-generation', data)
  }

  async getImageGenerationModels() {
    return this.get('/image-generation/models')
  }

  async getImageGenerationOptions() {
    return this.get('/image-generation/options')
  }

  // 图像编辑相关API
  async editImage(formData) {
    return this.post('/image-editing', formData)
  }

  async advancedImageEditing(formData) {
    return this.post('/image-editing/advanced', formData)
  }

  async upscaleImage(formData) {
    return this.post('/image-upscale', formData)
  }

  // 目标检测相关API
  async detectObjects(formData) {
    return this.post('/object-detection', formData)
  }

  async compareDetection(formData) {
    return this.post('/compare-detection', formData)
  }

  // 图像分割相关API
  async segmentImage(formData) {
    return this.post('/image-segmentation', formData)
  }

  async compareSegmentation(formData) {
    return this.post('/compare-segmentation', formData)
  }

  // 视频生成相关API
  async generateVideo(data) {
    return this.post('/video-generation', data)
  }

  async generateVideoFromImage(formData) {
    return this.post('/video-generation/from-image', formData)
  }

  async getVideoOptions() {
    return this.get('/video-generation/options')
  }

  // 工具API
  async testApiKey(apiKey) {
    return this.post('/test-api-key', { api_key: apiKey })
  }

  async validateContentMatch(formData) {
    return this.post('/validate-content-match', formData)
  }

  // 获取可用模型和选项
  async getModels() {
    return this.get('/models')
  }

  async getFeatures() {
    return this.get('/features')
  }
}

// 创建API服务实例
const apiService = new ApiService()

export default apiService
