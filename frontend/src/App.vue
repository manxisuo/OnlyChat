<template>
  <el-container style="height: 100vh;">
    <el-aside width="20%">
      <OnlineUsers :messages="messages" @selectUser="setCurrentRecipient" />
    </el-aside>
    <el-main v-if="currentRecipient">
      <el-dialog title="接收文件" :visible.sync="showReceiveProgress" :show-close="false" :close-on-click-modal="false" width="30%">
        <el-progress :percentage="receiveProgress" :format="format"></el-progress>
        <div>正在接收: {{currentReceivingFile}}</div>
      </el-dialog>
      <ChatArea :currentRecipient="currentRecipient" :messages="getMessages(currentRecipient)" @sendMessage="sendMessage" @sendFile="sendFile" />
    </el-main>
    <el-main v-else>
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
      currentReceivingFile: ''
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
        this.$socket.emit('send_message', { recipient: this.currentRecipient, message })
        if (!this.messages[this.currentRecipient]) {
          this.$set(this.messages, this.currentRecipient, { messages: [], unread: 0 })
        }
        this.messages[this.currentRecipient].messages.push({ sender: 'me', text: message })
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
    }
  },
  mounted() {
    this.$socket.on('receive_message', (data) => {
      if (!this.messages[data.sender]) {
        this.$set(this.messages, data.sender, { messages: [], unread: 0 })
      }
      this.messages[data.sender].messages.push({ sender: data.sender, text: data.message })
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
  }
}
</script>

<style>
#app {
  display: flex;
  height: 100vh;
}
.sidebar {
  width: 20%;
  border-right: 1px solid #ccc;
}
.main {
  width: 80%;
  display: flex;
  flex-direction: column;
}
</style>
