<template>
  <div class="message-input">
    <el-input v-model="message" @keyup.enter.native="sendMessage" placeholder="输入消息..." />
    <el-upload
      class="upload-demo"
      drag
      action=""
      :auto-upload="false"
      :on-change="sendFile">
      <i class="el-icon-upload"></i>
      <div class="el-upload__text">拖拽文件到此处，或<em>点击上传</em></div>
    </el-upload>
    <el-button type="primary" @click="sendMessage">发送</el-button>
    <el-dialog title="发送文件" :visible.sync="showSendProgress" :show-close="false" :close-on-click-modal="false" width="30%">
      <el-progress :percentage="sendProgress" :format="format"></el-progress>
      <div>正在发送: {{currentSendingFile}}</div>
    </el-dialog>
  </div>
</template>

<script>
export default {
  data() {
    return {
      message: '',
      chunkSize: 5 * 1024 * 1024,
      showSendProgress: false,
      sendProgress: 0,
      currentSendingFile: ''
    }
  },
  methods: {
    format(percentage) {
      return percentage === 100 ? '完成' : `${percentage}%`
    },
    sendMessage() {
      if (this.message.trim() !== '') {
        this.$emit('sendMessage', this.message)
        this.message = ''
      }
    },
    async sendFile(file) {
      const currentRecipient = this.$parent.$parent.currentRecipient
      if (!currentRecipient) {
        this.$message.error('请先选择接收者')
        return
      }

      console.log('Starting file transfer:', file.raw.name)  // 添加日志

      // 发送文件开始信息
      this.$socket.emit('send_file_start', {
        recipient: currentRecipient,
        fileInfo: {
          name: file.raw.name,
          size: file.raw.size,
          type: file.raw.type
        }
      })

      const totalChunks = Math.ceil(file.raw.size / this.chunkSize)
      const chunkTimeout = 15000;  // 增加到15秒
      let lastProgress = 0;

      this.showSendProgress = true
      this.sendProgress = 0
      this.currentSendingFile = file.raw.name
      
      try {
        for (let i = 0; i < totalChunks; i++) {
          const chunk = file.raw.slice(
            i * this.chunkSize,
            Math.min(file.raw.size, (i + 1) * this.chunkSize)
          )
          
          const chunkData = await new Promise((resolve) => {
            const reader = new FileReader()
            reader.onload = (e) => resolve(e.target.result)
            reader.readAsArrayBuffer(chunk)  // 改用 readAsArrayBuffer
          })

          await new Promise((resolve, reject) => {
            const timeoutId = setTimeout(() => {
              this.$socket.off('chunk_received', onReceived)
              this.$socket.off('chunk_error', onError)
              reject(new Error('发送超时，请重试'))
            }, chunkTimeout)

            const onReceived = (data) => {
              if (data.index === i) {
                clearTimeout(timeoutId)
                this.$socket.off('chunk_received', onReceived)
                this.$socket.off('chunk_error', onError)
                resolve()
              }
            }
            
            const onError = (data) => {
              if (data.index === i) {
                clearTimeout(timeoutId)
                this.$socket.off('chunk_received', onReceived)
                this.$socket.off('chunk_error', onError)
                reject(new Error(data.error))
              }
            }

            this.$socket.on('chunk_received', onReceived)
            this.$socket.on('chunk_error', onError)
            
            this.$socket.emit('send_file_chunk', {
              recipient: currentRecipient,
              chunk: {
                name: file.raw.name,
                data: chunkData,
                index: i,
                total: totalChunks
              }
            })
          })

          // 更新进度
          this.sendProgress = Math.round((i + 1) / totalChunks * 100)
          
          // 检查进度是否停滞
          if (this.sendProgress === lastProgress) {
            console.warn('Progress stalled, waiting...')
            await new Promise(resolve => setTimeout(resolve, 1000))
          }
          lastProgress = this.sendProgress

          // 每个块发送后稍微等待一下
          await new Promise(resolve => setTimeout(resolve, 100))
        }

        this.showSendProgress = false
        console.log('File transfer completed')
        this.$message({
          message: '文件发送完成',
          type: 'success'
        })
      } catch (error) {
        this.showSendProgress = false
        console.error('File transfer failed:', error)  // 添加错误日志
        this.$message.error('文件发送失败')
      }
    }
  }
}
</script>

<style>
.message-input {
  display: flex;
  align-items: center;
}
.message-input .el-input {
  flex: 1;
  margin-right: 10px;
}
</style>
