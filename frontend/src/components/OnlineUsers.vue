<template>
  <div>
    <el-card>
      <h2>在线用户</h2>
      <el-menu>
        <el-menu-item v-for="user in filteredUsers" :key="user" @click="selectUser(user)">
          {{ user }}
          <span v-if="messages[user] && messages[user].unread > 0" class="unread-count">{{ messages[user].unread }}</span>
        </el-menu-item>
      </el-menu>
    </el-card>
  </div>
</template>

<script>
export default {
  props: {
    messages: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      users: [],  // 确保初始化为数组
      clientIP: null
    }
  },
  computed: {
    filteredUsers() {
      return Array.isArray(this.users) ? this.users.filter(user => user !== this.clientIP) : []
    }
  },
  methods: {
    selectUser(user) {
      this.$emit('selectUser', user)
    }
  },
  mounted() {
    this.$socket.emit('client_ip', this.$clientIP)
    this.$socket.on('user_connected', (user) => {
      if (!this.users.includes(user)) {
        this.users.push(user)
      }
    })
    this.$socket.on('user_disconnected', (user) => {
      this.users = this.users.filter(u => u !== user)
    })
    this.$socket.on('update_user_list', (userList) => {
      // 确保收到的是数组
      this.users = Array.isArray(userList) ? userList : []
      console.log('Updated users list:', this.users)
    })
    this.$socket.on('your_ip', (ip) => {
      this.clientIP = ip
    })
  }
}
</script>

<style>
.unread-count {
  background-color: red;
  color: white;
  border-radius: 50%;
  padding: 2px 6px;
  margin-left: 10px;
}
</style>
