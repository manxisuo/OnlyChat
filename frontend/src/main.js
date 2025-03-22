import Vue from 'vue'
import App from './App.vue'
import io from 'socket.io-client'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'

Vue.config.productionTip = false

// 使用相对路径连接到后端服务器，并设置最大消息大小和启用二进制传输
Vue.prototype.$socket = io(window.location.origin, {
  maxHttpBufferSize: 100000000,  // 允许最大100MB的消息
  binary: true  // 启用二进制传输
})

Vue.use(ElementUI)

new Vue({
  render: h => h(App),
  mounted() {
    // 定时发送心跳信息
    setInterval(() => {
      this.$socket.emit('heartbeat')
    }, 3000)
  }
}).$mount('#app')
