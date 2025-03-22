<template>
  <el-card class="chat-area">
    <div class="messages">
      <div v-for="(message, index) in messages" :key="index">
        <strong>{{ message.sender }}:</strong> 
        <span v-if="message.file">
          <a :href="message.url" target="_blank">{{ message.file.name }}</a>
        </span>
        <span v-else>
          {{ message.text }}
        </span>
      </div>
    </div>
    <MessageInput @sendMessage="sendMessage" @sendFile="sendFile" />
  </el-card>
</template>

<script>
import MessageInput from './MessageInput.vue'

export default {
  components: {
    MessageInput
  },
  props: {
    currentRecipient: String,
    messages: Array
  },
  methods: {
    sendMessage(message) {
      this.$emit('sendMessage', message)
    },
    sendFile(file) {
      this.$emit('sendFile', file)
    }
  }
}
</script>

<style>
.chat-area {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  border-bottom: 1px solid #ccc;
}
</style>
