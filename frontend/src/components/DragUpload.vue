<template>
  <div class="drag-upload-container">
    <div 
      ref="dropZone"
      :class="[
        'border-2 border-dashed rounded-lg p-6 text-center transition-all duration-300',
        isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400',
        'cursor-pointer'
      ]"
      @click="triggerFileInput"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
    >
      <input 
        type="file" 
        ref="fileInput"
        @change="handleFileSelect"
        :accept="accept"
        class="hidden"
      >
      
      <div v-if="!preview" class="space-y-4">
        <div :class="['transition-colors', isDragOver ? 'text-blue-500' : 'text-gray-400']">
          <i class="fas fa-cloud-upload-alt text-4xl mb-4"></i>
        </div>
        <div>
          <p :class="['mb-2', isDragOver ? 'text-blue-600' : 'text-gray-600']">
            {{ isDragOver ? '松开鼠标上传文件' : (clickText || '点击上传图像或拖拽文件到此区域') }}
          </p>
          <p class="text-sm text-gray-500">{{ supportText || '支持 JPG, PNG, GIF 格式' }}</p>
        </div>
      </div>
      
      <div v-else class="relative">
        <img :src="preview" :class="previewClass" :alt="fileName">
        <button 
          @click.stop="clearFile"
          class="absolute top-2 right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm hover:bg-red-600 transition-colors"
        >
          ×
        </button>
        <div v-if="showFileName" class="mt-2 text-sm text-gray-600 truncate">
          {{ fileName }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'

export default {
  name: 'DragUpload',
  props: {
    accept: {
      type: String,
      default: 'image/*'
    },
    clickText: {
      type: String,
      default: ''
    },
    supportText: {
      type: String,
      default: ''
    },
    previewClass: {
      type: String,
      default: 'max-w-full h-80 object-contain mx-auto rounded-lg'
    },
    showFileName: {
      type: Boolean,
      default: false
    },
    maxSize: {
      type: Number,
      default: 10 * 1024 * 1024 // 10MB
    }
  },
  emits: ['file-selected', 'file-cleared', 'error'],
  setup(props, { emit }) {
    const dropZone = ref(null)
    const fileInput = ref(null)
    const isDragOver = ref(false)
    const preview = ref('')
    const fileName = ref('')
    const selectedFile = ref(null)
    
    let dragCounter = 0

    const validateFile = (file) => {
      // 检查文件大小
      if (file.size > props.maxSize) {
        emit('error', `文件大小不能超过 ${(props.maxSize / 1024 / 1024).toFixed(1)}MB`)
        return false
      }
      
      // 检查文件类型
      if (props.accept !== '*' && !file.type.match(props.accept.replace('*', '.*'))) {
        emit('error', '不支持的文件格式')
        return false
      }
      
      return true
    }

    const processFile = (file) => {
      if (!validateFile(file)) {
        return
      }
      
      selectedFile.value = file
      fileName.value = file.name
      
      // 如果是图像文件，生成预览
      if (file.type.startsWith('image/')) {
        const reader = new FileReader()
        reader.onload = (e) => {
          preview.value = e.target.result
        }
        reader.readAsDataURL(file)
      } else {
        preview.value = ''
      }
      
      emit('file-selected', file)
    }

    const handleDragOver = (e) => {
      e.preventDefault()
      dragCounter++
      isDragOver.value = true
    }

    const handleDragLeave = (e) => {
      e.preventDefault()
      dragCounter--
      if (dragCounter === 0) {
        isDragOver.value = false
      }
    }

    const handleDrop = (e) => {
      e.preventDefault()
      dragCounter = 0
      isDragOver.value = false
      
      const files = e.dataTransfer.files
      if (files.length > 0) {
        processFile(files[0])
      }
    }

    const handleFileSelect = (e) => {
      const files = e.target.files
      if (files.length > 0) {
        processFile(files[0])
      }
    }

    const triggerFileInput = () => {
      if (fileInput.value) {
        fileInput.value.click()
      }
    }

    const clearFile = () => {
      selectedFile.value = null
      preview.value = ''
      fileName.value = ''
      if (fileInput.value) {
        fileInput.value.value = ''
      }
      emit('file-cleared')
    }

    // 防止页面默认的拖拽行为
    const preventDefaults = (e) => {
      e.preventDefault()
      e.stopPropagation()
    }

    onMounted(() => {
      // 防止整个页面的拖拽默认行为
      ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        document.addEventListener(eventName, preventDefaults, false)
      })
    })

    onUnmounted(() => {
      ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        document.removeEventListener(eventName, preventDefaults, false)
      })
    })

    return {
      dropZone,
      fileInput,
      isDragOver,
      preview,
      fileName,
      selectedFile,
      handleDragOver,
      handleDragLeave,
      handleDrop,
      handleFileSelect,
      triggerFileInput,
      clearFile
    }
  }
}
</script>

<style scoped>
.drag-upload-container {
  width: 100%;
}

.drag-upload-container .border-dashed {
  transition: all 0.3s ease;
}

.drag-upload-container .border-dashed:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>