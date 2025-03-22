<template>
  <div class="online-users">
    <div class="users-header">
      <el-card class="users-card">
        <div class="header">
          <div class="title">
            <i class="el-icon-user"></i>
            <span>在线用户</span>
            <el-badge :value="filteredUsers.length" class="users-count" type="primary" />
          </div>
          <div class="my-ip" v-if="clientIP">
            <el-tooltip content="点击修改昵称" placement="right">
              <el-tag size="small" effect="dark" type="info" @click="showNicknameDialog">
                <i class="el-icon-position"></i>
                {{ nickname }}
              </el-tag>
            </el-tooltip>
          </div>
        </div>
      </el-card>
    </div>
    
    <div class="users-list-container">
      <el-menu class="users-list">
        <el-menu-item v-for="user in filteredUsers" 
                      :key="user.ip" 
                      @click="selectUser(user)"
                      :class="{ 'active-user': user.ip === selectedUser }">
          <div class="user-item">
            <div class="user-avatar">
              <el-avatar size="small">{{ (user.nickname || user.ip)?.slice(-2) || '?' }}</el-avatar>
            </div>
            <div class="user-info">
              <span class="user-ip">{{ user.nickname || user.ip }}</span>
              <span class="user-real-ip">({{ user.ip }})</span>
              <el-badge v-if="messages[user.ip] && messages[user.ip].unread > 0" 
                       :value="messages[user.ip].unread" 
                       class="unread-badge" />
            </div>
          </div>
        </el-menu-item>
      </el-menu>
    </div>
    
    <!-- 昵称修改对话框 -->
    <el-dialog title="修改昵称" :visible.sync="nicknameDialogVisible" width="30%">
      <el-form>
        <el-form-item>
          <el-input v-model="newNickname" placeholder="请输入新昵称"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="nicknameDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="updateNickname">确定</el-button>
      </span>
    </el-dialog>
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
      users: [],
      clientIP: null,
      selectedUser: null,
      nickname: '',
      nicknameDialogVisible: false,
      newNickname: ''
    }
  },
  computed: {
    filteredUsers() {
      return Array.isArray(this.users) ? this.users.filter(user => user.ip !== this.clientIP) : []
    }
  },
  methods: {
    selectUser(user) {
      this.selectedUser = user.ip
      // 只发送用户的 IP，避免传递整个用户对象
      this.$emit('selectUser', user.ip)
    },
    showNicknameDialog() {
      this.newNickname = this.nickname
      this.nicknameDialogVisible = true
    },
    updateNickname() {
      if (this.newNickname.trim()) {
        this.$socket.emit('update_nickname', { nickname: this.newNickname })
        this.nicknameDialogVisible = false
      }
    }
  },
  mounted() {
    this.$socket.emit('client_ip', this.$clientIP)
    this.$socket.on('user_connected', (user) => {
      if (!this.users.some(u => u.ip === user.ip)) {
        this.users.push(user)
      }
    })
    this.$socket.on('user_disconnected', (user) => {
      this.users = this.users.filter(u => u.ip !== user.ip)
    })
    this.$socket.on('update_user_list', (userList) => {
      this.users = Array.isArray(userList) ? userList : []
      console.log('Updated users list:', this.users)
    })
    this.$socket.on('your_ip', (data) => {
      this.clientIP = data.ip
      this.nickname = data.nickname
    })
    this.$socket.on('nickname_updated', (data) => {
      // 更新用户列表中的昵称
      this.users = this.users.map(user => {
        if (user.ip === data.ip) {
          return { ...user, nickname: data.nickname }
        }
        return user
      })
      // 如果是自己的昵称被更新
      if (data.ip === this.clientIP) {
        this.nickname = data.nickname
      }
    })
  }
}
</script>

<style scoped>
.online-users {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.users-header {
  flex: 0 0 auto;
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
}

.users-list-container {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.users-list {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: auto;
  border: none;
  padding: 10px;
}

.users-card {
  height: calc(100% - 20px);
  background: #f8f9fa;
}

.header {
  padding: 15px 0;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 15px;
}

.title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 15px;
}

.title i {
  margin-right: 8px;
  color: #409EFF;
}

.users-count {
  margin-left: 10px;
}

.my-ip {
  padding: 5px 0;
}

.user-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.user-avatar {
  margin-right: 12px;
}

.user-info {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-ip {
  color: #606266;
  font-size: 14px;
}

.user-real-ip {
  color: #909399;
  font-size: 12px;
  margin-left: 4px;
}

.active-user {
  background-color: #ecf5ff !important;
  border-radius: 4px;
}

.unread-badge {
  margin-left: auto;
}

.el-menu-item {
  height: auto;
  line-height: 1.5;
  padding: 5px 15px;
  margin: 5px 0;
  border-radius: 4px;
}

.el-menu-item:hover {
  background-color: #f5f7fa !important;
}

/* 移动端适配 */
@media screen and (max-width: 768px) {
  .online-users {
    max-height: 40vh;
    min-height: 0;
  }

  .users-header {
    padding: 8px;
  }

  .header {
    padding: 8px 0;
    margin-bottom: 8px;
  }

  .users-list {
    max-height: calc(40vh - 100px);
  }
}
</style>
