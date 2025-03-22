<template>
  <el-container class="app-container">
    <div class="side-collapse-btn" :class="{ collapsed: sidebarCollapsed }" @click="toggleSidebar">
      <i :class="sidebarCollapsed ? 'el-icon-d-arrow-right' : 'el-icon-d-arrow-left'"></i>
    </div>
    <el-aside :width="sidebarCollapsed ? '0' : '280px'" class="users-aside">
      <OnlineUsers :messages="messages" @selectUser="setCurrentRecipient" />
    </el-aside>
    <el-main class="chat-main" v-if="currentRecipient">
      <el-dialog title="接收文件" :visible.sync="showReceiveProgress" :show-close="false" :close-on-click-modal="false" width="30%">
        <el-progress :percentage="receiveProgress" :format="format"></el-progress>
        <div>正在接收: {{currentReceivingFile}}</div>
      </el-dialog>
      <ChatArea :currentRecipient="currentRecipient" :messages="getMessages(currentRecipient)" @sendMessage="sendMessage" @sendFile="sendFile" />
    </el-main>
    <el-main class="empty-state" v-else>
      <p>请选择一个用户开始聊天</p>
    </el-main>
  </el-container>
</template>

<script>
import OnlineUsers from './components/OnlineUsers.vue'
import ChatArea from './components/ChatArea.vue'

export default {
  name: 'App',
  components: {
    OnlineUsers,
    ChatArea
  },
  data() {
    return {
      currentRecipient: null,
      messages: {},
      fileChunks: {},
      fileInfo: {},
      showReceiveProgress: false,
      receiveProgress: 0,
      currentReceivingFile: '',
      fileWriters: new Map(),
      fileBuffers: new Map(),
      users: [],  // 添加 users 数组用于存储用户列表
      sidebarCollapsed: false
    }
  },
  methods: {
    setCurrentRecipient(user) {
      this.currentRecipient = user
      if (this.messages[this.currentRecipient]) {
        this.messages[this.currentRecipient].unread = 0
      }
    },
    sendMessage(message) {
      if (this.currentRecipient) {
        if (typeof message === 'object') {
          if (message.type === 'progress') {
            // 处理进度条类型消息
            if (!this.messages[this.currentRecipient]) {
              this.$set(this.messages, this.currentRecipient, { messages: [], unread: 0 })
            }
            this.messages[this.currentRecipient].messages.push(message)
          } else if (message.type === 'markdown') {
            // 处理markdown类型消息
            this.$socket.emit('send_message', { recipient: this.currentRecipient, message: message.content })
            if (!this.messages[this.currentRecipient]) {
              this.$set(this.messages, this.currentRecipient, { messages: [], unread: 0 })
            }
            this.messages[this.currentRecipient].messages.push({ 
              sender: 'me', 
              type: 'markdown',
              content: message.content
            })
          }
        } else {
          // 处理普通文本消息
          this.$socket.emit('send_message', { recipient: this.currentRecipient, message })
          if (!this.messages[this.currentRecipient]) {
            this.$set(this.messages, this.currentRecipient, { messages: [], unread: 0 })
          }
          this.messages[this.currentRecipient].messages.push({ sender: 'me', text: message })
        }
      }
    },
    sendFile(file) {
      if (this.currentRecipient) {
        this.$socket.emit('send_file', { recipient: this.currentRecipient, file })
      }
    },
    getMessages(recipient) {
      return this.messages[recipient] ? this.messages[recipient].messages : []
    },
    async saveFile(name, chunks) {
      try {
        const fileType = this.fileInfo[name]?.type || 'application/octet-stream'
        
        // 检查和转换数据类型
        const processedChunks = chunks.map(chunk => {
          if (chunk instanceof ArrayBuffer) {
            return chunk
          } else if (typeof chunk === 'string') {
            // 如果是Base64字符串，进行转换
            const base64 = chunk.replace(/^data:[^;]+;base64,/, '')
            const binary = atob(base64)
            const bytes = new Uint8Array(binary.length)
            for (let i = 0; i < binary.length; i++) {
              bytes[i] = binary.charCodeAt(i)
            }
            return bytes.buffer
          } else {
            throw new Error('不支持的数据类型')
          }
        })

        // 创建blob并下载
        const blob = new Blob(processedChunks, { type: fileType })
        
        // 针对移动端的处理
        if (/mobile/i.test(navigator.userAgent)) {
          // 移动端使用新标签页打开
          window.open(URL.createObjectURL(blob))
        } else {
          // PC端使用下载
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = name
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
          URL.revokeObjectURL(url)
        }

        console.log('文件保存成功:', name)
      } catch (err) {
        console.error('保存文件失败:', err)
        this.$message.error(`保存文件失败: ${err.message}`)
      }
    },
    format(percentage) {
      return percentage === 100 ? '完成' : `${percentage}%`
    },
    initFileStream(name, type) {
      const chunks = []
      
      const writableStream = new WritableStream({
        write(chunk) {
          chunks.push(chunk)
          return new Promise(resolve => setTimeout(resolve, 0)) // 避免UI阻塞
        },
        close() {
          const blob = new Blob(chunks, { type })
          const url = URL.createObjectURL(blob)
          
          if (/mobile/i.test(navigator.userAgent)) {
            window.open(url)
          } else {
            const a = document.createElement('a')
            a.href = url
            a.download = name
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
          }
          URL.revokeObjectURL(url)
        }
      })

      return writableStream.getWriter()
    },
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    }
  },
  mounted() {
    // 添加用户列表更新事件的处理
    this.$socket.on('update_user_list', (userList) => {
      this.users = Array.isArray(userList) ? userList : []
    })

    this.$socket.on('user_connected', (user) => {
      if (!this.users.some(u => u.ip === user.ip)) {
        this.users.push(user)
      }
    })

    this.$socket.on('user_disconnected', (user) => {
      this.users = this.users.filter(u => u.ip !== user.ip)
    })

    this.$socket.on('nickname_updated', (data) => {
      const userIndex = this.users.findIndex(u => u.ip === data.ip)
      if (userIndex !== -1) {
        this.users[userIndex].nickname = data.nickname
      }
    })

    this.$socket.on('receive_message', (data) => {
      if (!this.messages[data.sender]) {
        this.$set(this.messages, data.sender, { messages: [], unread: 0 })
      }
      // 判断是否包含markdown标记
      const hasMarkdown = data.message.includes('#') || 
                        data.message.includes('```') ||
                        data.message.includes('*') ||
                        data.message.includes('_') ||
                        data.message.includes('- ');
      
      // 获取发送者昵称
      const senderUser = this.users.find(u => u.ip === data.sender)
      const senderNickname = senderUser ? senderUser.nickname : data.sender
      
      if (hasMarkdown) {
        this.messages[data.sender].messages.push({ 
          sender: { ip: data.sender, nickname: senderNickname },
          type: 'markdown',
          content: data.message
        })
      } else {
        this.messages[data.sender].messages.push({ 
          sender: { ip: data.sender, nickname: senderNickname },
          text: data.message 
        })
      }
      
      if (this.currentRecipient !== data.sender) {
        this.messages[data.sender].unread += 1
      }
    })
    this.$socket.on('receive_file_start', (data) => {
      const { sender, fileInfo } = data
      this.fileInfo[fileInfo.name] = fileInfo
      // 初始化文件块存储
      this.$set(this.fileChunks, fileInfo.name, {
        chunks: [],
        total: Math.ceil(fileInfo.size / (256 * 1024)), // 使用相同的块大小
        received: 0
      })
      this.showReceiveProgress = true
      this.receiveProgress = 0
      this.currentReceivingFile = fileInfo.name
      console.log('Started receiving file:', fileInfo.name)
    })

    this.$socket.on('receive_file_chunk', (data) => {
      try {
        const { sender, chunk } = data
        const { name, data: chunkData, index, total } = chunk
        
        console.log(`Receiving chunk ${index}/${total} for file ${name}`)

        if (!this.fileChunks[name]) {
          // 如果文件块存储不存在，重新初始化
          this.$set(this.fileChunks, name, {
            chunks: [],
            total: total,
            received: 0
          })
        }
        
        // 直接存储 ArrayBuffer 数据
        this.fileChunks[name].chunks[index] = chunkData
        this.fileChunks[name].received++
        
        // 更新进度
        this.receiveProgress = Math.round((this.fileChunks[name].received / total) * 100)
        
        // 检查是否接收完成
        if (this.fileChunks[name].received === total) {
          console.log(`File ${name} complete, preparing to save...`)
          const chunks = this.fileChunks[name].chunks
          this.showReceiveProgress = false
          this.saveFile(name, chunks)

          // 清理内存
          this.$delete(this.fileChunks, name)
          this.$delete(this.fileInfo, name)

          // 添加消息记录
          if (!this.messages[sender]) {
            this.$set(this.messages, sender, { messages: [], unread: 0 })
          }
          this.messages[sender].messages.push({
            sender: sender,
            text: `文件: ${name}已接收`
          })
        }

      } catch (error) {
        console.error('Error processing chunk:', error)
        this.$message.error(`处理文件块失败: ${error.message}`)
      }
    })
    this.$socket.on('file_start', async (data) => {
      const { sender, fileInfo } = data
      // 确保初始化正确的fileInfo
      this.fileInfo[fileInfo.name] = fileInfo
      // 使用实际的文件大小初始化接收缓冲区
      this.fileBuffers.set(fileInfo.name, {
        received: 0,
        total: parseInt(fileInfo.size) // 确保是数字
      })
      const writer = await this.initFileStream(fileInfo.name, fileInfo.type)
      this.fileWriters.set(fileInfo.name, writer)
      
      this.showReceiveProgress = true
      this.currentReceivingFile = fileInfo.name
      this.receiveProgress = 0
      console.log('Started receiving file:', fileInfo.name, 'size:', fileInfo.size)
    })

    this.$socket.on('file_data', async (data) => {
      try {
        const { sender, name, data: chunk } = data
        const writer = this.fileWriters.get(name)
        const buffer = this.fileBuffers.get(name)
        
        if (writer && buffer) {
          await writer.write(chunk)
          buffer.received += chunk.byteLength // 使用byteLength而不是length
          const progress = Math.min(100, Math.round((buffer.received / buffer.total) * 100))
          this.receiveProgress = progress
          console.log(`Progress: ${buffer.received}/${buffer.total} bytes (${progress}%)`)
        }
      } catch (error) {
        console.error('Error processing chunk:', error)
        this.$message.error(`处理文件块失败: ${error.message}`)
      }
    })

    this.$socket.on('file_end', async (data) => {
      const { sender, name } = data
      const writer = this.fileWriters.get(name)
      
      if (writer) {
        await writer.close()
        this.fileWriters.delete(name)
        this.fileBuffers.delete(name)
        this.showReceiveProgress = false
        
        if (!this.messages[sender]) {
          this.$set(this.messages, sender, { messages: [], unread: 0 })
        }
        this.messages[sender].messages.push({
          sender: sender,
          text: `文件: ${name}已接收`
        })
      }
    })
  }
}
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100vh;
  height: -webkit-fill-available;  /* 适配移动端 */
  overflow: hidden;
}

.app-container {
  height: 100vh;
  height: -webkit-fill-available;  /* 适配移动端 */
  width: 100vw;
  overflow: hidden;
  display: flex;
  flex-direction: row;
}

.users-aside {
  border-right: 1px solid #dcdfe6;
  background: #fff;
  height: 100vh;
  overflow: hidden;
  transition: width 0.3s;
}

.chat-main {
  padding: 0;
  height: 100vh;
  overflow: hidden;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 16px;
}

.side-collapse-btn {
  position: fixed;
  left: 280px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 60px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-left: none;
  border-radius: 0 4px 4px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 100;
  transition: left 0.3s;
}

.side-collapse-btn.collapsed {
  left: 0;
}

.side-collapse-btn:hover {
  background: #f5f7fa;
}

.side-collapse-btn i {
  color: #909399;
}

/* 添加移动端适配 */
@media screen and (max-width: 768px) {
  .app-container {
    flex-direction: column;
  }

  .users-aside {
    width: 100% !important;
    height: auto !important;
    max-height: 40vh;
  }

  .chat-main {
    height: 60vh !important;
    width: 100% !important;
  }

  .empty-state {
    height: 60vh !important;
  }

  .side-collapse-btn {
    display: none;  /* 移动端不显示侧边栏折叠按钮 */
  }
}
</style>
