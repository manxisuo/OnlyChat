<template>
  <div class="message-input">
    <div class="input-area">
      <!-- 普通文本模式 -->
      <el-input v-if="!isMarkdownMode"
                v-model="message"
                type="textarea"
                :rows="3"
                @keydown.enter.native="handleEnter"
                @keydown.enter.native.ctrl.prevent="sendMessage"
                placeholder="输入消息... (Ctrl + Enter 发送，Enter 换行)" />

      <!-- Markdown模式 -->
      <editor v-else
              ref="editor"
              :initialValue="message"
              :options="editorOptions"
              height="150px"
              @change="handleChange"
              @keydown="handleEditorKeydown" />

      <div class="action-buttons">
        <div class="left-buttons">
          <el-checkbox v-model="isMarkdownMode">
            <el-tooltip content="切换Markdown编辑模式" placement="top">
              <span>Markdown模式</span>
            </el-tooltip>
          </el-checkbox>
        </div>
        <div class="right-buttons">
          <el-upload
            class="upload-inline"
            action=""
            :auto-upload="false"
            :show-file-list="false"
            :on-change="sendFile">
            <el-button icon="el-icon-paperclip" type="text"></el-button>
          </el-upload>
          <el-button type="primary" @click="sendMessage">发送</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Editor } from '@toast-ui/vue-editor'
import 'codemirror/lib/codemirror.css'
import '@toast-ui/editor/dist/toastui-editor.css'

export default {
  components: {
    editor: Editor
  },
  props: {
    currentRecipient: String  // 添加 prop
  },
  data() {
    return {
      message: '',
      isMarkdownMode: false,
      currentSendingFile: '',
      abortController: null,
      editorOptions: {
        hideModeSwitch: true,
        toolbarItems: [],
        placeholder: '输入消息... (Ctrl + Enter 发送，Enter 换行)'
      }
    }
  },
  methods: {
    format(percentage) {
      return percentage === 100 ? '完成' : `${percentage}%`
    },
    handleEnter(e) {
      if (e.ctrlKey) {
        e.preventDefault()
        this.sendMessage()
      }
      // 普通 Enter 键不处理，让它自然换行
    },
    handleChange() {
      if (this.isMarkdownMode) {
        this.message = this.$refs.editor.invoke('getMarkdown')
      }
    },
    handleEditorKeydown(event) {
      if (event.key === 'Enter' && event.ctrlKey) {
        event.preventDefault()
        this.sendMessage()
      }
    },
    sendMessage() {
      const message = this.message.trim()
      if (message) {
        this.$emit('sendMessage', this.isMarkdownMode ? {
          type: 'markdown',
          content: message
        } : message)

        // 清空输入
        if (this.isMarkdownMode) {
          this.$refs.editor.invoke('setMarkdown', '')
        }
        this.message = ''
      }
    },
    async sendFile(file) {
      if (!this.currentRecipient) {  // 使用 prop
        this.$message.error('请先选择接收者')
        return
      }

      // 添加进度条消息
      const progressMessage = {
        sender: 'me',
        type: 'progress',
        fileName: file.raw.name,
        progress: 0,
        status: ''
      }
      this.$emit('sendMessage', progressMessage)

      try {
        // 创建 ReadableStream
        const stream = file.raw.stream()
        const reader = stream.getReader()
        const fileSize = parseInt(file.raw.size)
        let bytesRead = 0

        // 发送文件信息
        this.$socket.emit('file_start', {
          recipient: this.currentRecipient,  // 使用 prop
          fileInfo: {
            name: file.raw.name,
            size: fileSize,
            type: file.raw.type
          }
        })

        // 开始读取流
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          // 发送数据块
          await new Promise((resolve, reject) => {
            const timeoutId = setTimeout(() => reject(new Error('发送超时')), 5000)

            this.$socket.emit('file_data', {
              recipient: this.currentRecipient,  // 使用 prop
              name: file.raw.name,
              data: value
            }, () => {
              clearTimeout(timeoutId)
              resolve()
            })
          })

          bytesRead += value.byteLength // 使用byteLength而不是length
          const progress = Math.min(100, Math.round((bytesRead / fileSize) * 100))
          
          // 更新进度条消息
          progressMessage.progress = progress
          if (progress === 100) {
            progressMessage.status = 'success'
          }
        }

        // 发送完成信号
        this.$socket.emit('file_end', {
          recipient: this.currentRecipient,  // 使用 prop
          name: file.raw.name
        })

        // 添加完成消息
        this.$emit('sendMessage', `文件: ${file.raw.name}已发送`)

      } catch (error) {
        // 更新进度条状态为失败
        progressMessage.status = 'exception'
        progressMessage.progress = 100
        
        console.error('文件发送失败:', error)
        this.$message.error('文件发送失败')
      }
    }
  },
  watch: {
    isMarkdownMode(newVal) {
      // 切换模式时保留内容
      this.$nextTick(() => {
        if (newVal && this.$refs.editor) {
          this.$refs.editor.invoke('setMarkdown', this.message)
        }
      })
    }
  }
}
</script>

<style scoped>
.message-input {
  width: 100%;
  box-sizing: border-box;  /* 确保padding计入宽度 */
}

.input-area {
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
}

.action-buttons {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px;
  border-top: 1px solid #ebeef5;
}

.left-buttons, .right-buttons {
  display: flex;
  align-items: center;
}

.right-buttons {
  gap: 8px;
}

:deep(.toastui-editor-defaultUI) {
  border: none;
  max-height: 200px;  /* 设置最大高度 */
}

:deep(.toastui-editor-defaultUI .ProseMirror) {
  min-height: 130px;  /* 设置最小高度 */
  padding: 12px 15px;  /* 调整内边距 */
}

.input-area :deep(.el-input) {
  width: 100%;  /* 确保输入框占满剩余空间 */
}

.input-area :deep(.el-input__inner) {
  border-right: none;
  padding-right: 0;
}

.input-area :deep(.el-input-group__append) {
  white-space: nowrap;  /* 防止按钮换行 */
  position: relative;  /* 确保显示在正确位置 */
  right: 0;
}

.upload-inline {
  display: inline-flex;  /* 改为inline-flex */
  align-items: center;
  border-left: 1px solid #DCDFE6;
  height: 32px;
  padding: 0 8px;
  margin: 0;
}

.upload-inline :deep(.el-upload) {
  display: block;
}

.upload-inline :deep(.el-upload-dragger) {
  display: none;
}

.upload-inline :deep(.el-button) {
  height: 32px;
  padding: 8px 12px;
  border: none;
  border-radius: 0;
}

.upload-inline :deep(.el-icon-paperclip) {
  font-size: 18px;
  color: #909399;
}

.upload-inline :deep(.el-button):hover .el-icon-paperclip {
  color: #409EFF;
}

.el-button {
  height: 32px;
  margin: 0;
  padding: 8px 15px;
  border: none;
  font-size: 14px;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-textarea__inner) {
  border: none;
  resize: none;
  min-height: 130px;
  padding: 12px 15px;
}

:deep(.el-checkbox) {
  margin-right: 16px;
}
</style>
