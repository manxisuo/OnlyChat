<template>
  <div class="chat-area">
    <div class="chat-header">
      <div class="recipient-info">
        <el-avatar size="small">{{ recipientNickname?.slice(-2) }}</el-avatar>
        <span class="recipient-ip">{{ recipientNickname }}</span>
        <span class="recipient-real-ip">({{ currentRecipient }})</span>
        <el-tag size="mini" type="success">在线</el-tag>
      </div>
    </div>

    <div class="chat-main">
      <div class="messages-container">
        <div class="messages" ref="messageContainer">
          <div v-for="(message, index) in messages" 
               :key="index"
               :class="['message-item', message.sender === 'me' ? 'message-right' : 'message-left']">
            <div class="message-content">
              <div class="message-sender" v-if="message.sender !== 'me'">
                <el-avatar size="small">{{ message.sender.nickname?.slice(-2) }}</el-avatar>
                <span>{{ message.sender.nickname }}</span>
              </div>
              <div class="message-bubble" :class="{ 
                'has-markdown': message.type === 'markdown',
                'has-progress': message.type === 'progress'
              }">
                <template v-if="message.type === 'progress'">
                  <div class="progress-message">
                    <div class="progress-info">
                      <i class="el-icon-upload2"></i>
                      <span>正在发送: {{ message.fileName }}</span>
                    </div>
                    <el-progress 
                      :percentage="message.progress"
                      :status="message.status"
                      :show-text="true">
                    </el-progress>
                  </div>
                </template>
                <template v-else-if="message.file">
                  <div class="file-message">
                    <i class="el-icon-document"></i>
                    <a :href="message.url" target="_blank">{{ message.file.name }}</a>
                  </div>
                </template>
                <template v-else-if="message.type === 'markdown'">
                  <div class="markdown-content" v-html="renderMarkdown(message.content)"></div>
                </template>
                <template v-else>
                  {{ message.text }}
                </template>
              </div>
              <div class="message-time">
                {{ new Date().toLocaleTimeString() }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="input-collapse-btn" @click="toggleInput">
        <i :class="inputCollapsed ? 'el-icon-caret-bottom' : 'el-icon-caret-top'"></i>
      </div>
      <div class="input-container" :class="{ collapsed: inputCollapsed }">
        <MessageInput 
          :currentRecipient="currentRecipient"
          @sendMessage="sendMessage" 
          @sendFile="sendFile" />
      </div>
    </div>
  </div>
</template>

<script>
import MessageInput from './MessageInput.vue'
import MarkdownIt from 'markdown-it'

export default {
  components: {
    MessageInput
  },
  props: {
    currentRecipient: String,
    messages: Array
  },
  data() {
    return {
      md: new MarkdownIt(),
      recipientNickname: '',  // 添加昵称状态
      inputCollapsed: false
    }
  },
  mounted() {
    // 处理昵称更新
    this.$socket.on('nickname_updated', (data) => {
      if (data.ip === this.currentRecipient) {
        this.recipientNickname = data.nickname || data.ip
      }
    })
  },
  watch: {
    currentRecipient: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          // 获取用户昵称，如果找不到则使用 IP
          const users = this.$parent.$data.users || []
          const user = users.find(u => u.ip === newVal)
          this.recipientNickname = user?.nickname || newVal
        } else {
          this.recipientNickname = ''
        }
      }
    }
  },
  methods: {
    sendMessage(message) {
      if (typeof message === 'object' && message.type === 'markdown') {
        this.$emit('sendMessage', {
          type: 'markdown',
          content: message.content
        })
      } else {
        this.$emit('sendMessage', message)
      }
    },
    sendFile(file) {
      this.$emit('sendFile', file)
    },
    renderMarkdown(text) {
      return this.md.render(text)
    },
    toggleInput() {
      this.inputCollapsed = !this.inputCollapsed
    }
  }
}
</script>

<style scoped>
.chat-area {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.chat-header {
  flex: 0 0 auto;
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
  background: #fff;
  z-index: 1;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  position: relative;
}

.messages-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.messages {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: auto;
  padding: 20px;
}

.input-collapse-btn {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 20px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-bottom: none;
  border-radius: 4px 4px 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
}

.input-collapse-btn:hover {
  background: #f5f7fa;
}

.input-collapse-btn i {
  color: #909399;
}

.input-container {
  flex: 0 0 auto;
  border-top: 1px solid #ebeef5;
  background: #fff;
  padding: 12px 20px;
  transition: transform 0.3s;
}

.input-container.collapsed {
  transform: translateY(calc(100% - 40px));
}

.recipient-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.recipient-ip {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.message-item {
  margin: 15px 0;
  display: flex;
}

.message-right {
  justify-content: flex-end;
}

.message-content {
  max-width: 70%;
}

.message-sender {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
  font-size: 12px;
  color: #909399;
}

.message-bubble {
  padding: 10px 15px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  word-break: break-word;
}

.message-right .message-bubble {
  background: #409EFF;
  color: #fff;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  text-align: right;
}

.file-message {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-message i {
  font-size: 20px;
}

.file-message a {
  color: inherit;
  text-decoration: none;
}

.message-input {
  padding: 15px;
  background: #fff;
  border-top: 1px solid #ebeef5;
}

.progress-message {
  min-width: 200px;
  padding: 5px;
}

.progress-info {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 8px;
}

.progress-info i {
  font-size: 18px;
}

.message-right .progress-message {
  color: #fff;
}

.message-right :deep(.el-progress__text) {
  color: #fff;
}

.markdown-content {
  line-height: 1.6;
}

.markdown-content :deep(p) {
  margin: 0;
}

.markdown-content :deep(pre) {
  background: #f8f9fa;
  padding: 8px;
  border-radius: 4px;
  margin: 8px 0;
}

.markdown-content :deep(code) {
  background: #f8f9fa;
  padding: 2px 4px;
  border-radius: 3px;
}

.message-right .markdown-content :deep(code) {
  background: rgba(255, 255, 255, 0.1);
}

.message-right .markdown-content :deep(pre),
.message-right .markdown-content :deep(code) {
  background: rgba(0, 0, 0, 0.2);  /* 深色背景 */
  color: #fff;  /* 白色文字 */
}

.message-right .markdown-content :deep(pre) {
  border: 1px solid rgba(255, 255, 255, 0.1);  /* 添加subtle边框 */
}

.markdown-content :deep(pre) {
  padding: 12px;
  border-radius: 6px;
  margin: 8px 0;
  overflow-x: auto;  /* 添加水平滚动 */
}

.markdown-content :deep(code) {
  font-family: Consolas, Monaco, 'Andale Mono', monospace;
  padding: 2px 4px;
  border-radius: 3px;
}

/* 普通消息的代码块样式 */
.message-left .markdown-content :deep(pre),
.message-left .markdown-content :deep(code) {
  background: #f8f9fa;
  color: #333;
}

.message-right .message-bubble.has-markdown {
  background: #fff;
  color: #333;
  border: 1px solid #ebeef5;
}

.message-right .markdown-content :deep(pre),
.message-right .markdown-content :deep(code) {
  background: #f8f9fa;  /* 和左侧消息一致的背景色 */
  color: #333;  /* 和左侧消息一致的文字颜色 */
  border: 1px solid #ebeef5;
}

.markdown-content :deep(pre) {
  padding: 12px;
  border-radius: 6px;
  margin: 8px 0;
  overflow-x: auto;
}

.markdown-content :deep(code) {
  font-family: Consolas, Monaco, 'Andale Mono', monospace;
  padding: 2px 4px;
  border-radius: 3px;
}

/* 确保进度条和普通文本消息保持原有的蓝色样式 */
.message-right .message-bubble:not(.has-markdown) {
  background: #409EFF;
  color: #fff;
}

/* 进度条消息的样式 */
.message-right .message-bubble.has-progress {
  background: #fff;
  color: #333;
  border: 1px solid #ebeef5;
}

.message-right .has-progress .progress-info {
  color: #606266;  /* 深色文字 */
}

.message-right .has-progress :deep(.el-progress__text) {
  color: #606266;  /* 深色文字 */
}

.message-right .has-progress :deep(.el-progress-bar__outer) {
  background-color: #f0f2f5;  /* 浅色背景 */
}

.message-right .has-progress :deep(.el-progress-bar__inner) {
  background-color: #409EFF;  /* 蓝色进度条 */
}

/* 进度条成功状态 */
.message-right .has-progress :deep(.el-progress.is-success .el-progress-bar__inner) {
  background-color: #67C23A;  /* 成功状态为绿色 */
}

/* 进度条失败状态 */
.message-right .has-progress :deep(.el-progress.is-exception .el-progress-bar__inner) {
  background-color: #F56C6C;  /* 失败状态为红色 */
}

.recipient-real-ip {
  color: #909399;
  font-size: 14px;
  margin-left: 4px;
}

/* 移动端适配 */
@media screen and (max-width: 768px) {
  .chat-area {
    height: 60vh;
    max-height: -webkit-fill-available;
  }

  .messages-container {
    flex: 1 1 0;
    min-height: 0;
  }

  .messages {
    padding: 10px;
  }

  .input-container {
    position: relative;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 8px;
  }

  .input-container.collapsed {
    transform: translateY(calc(100% - 50px));
  }

  .message-content {
    max-width: 85%;
  }
}
</style>
