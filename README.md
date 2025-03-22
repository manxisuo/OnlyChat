# OnlyChat

OnlyChat 是一个基于 Vue.js 和 Flask 的实时聊天应用，支持点对点通信、Markdown 消息、文件传输等功能。

## 功能特点

- 🚀 基于 WebSocket 的实时通信
- 👥 用户在线状态实时显示
- 📝 支持 Markdown 格式消息
- 📎 支持文件传输
- 📱 响应式设计，支持移动端
- 🏷️ 支持自定义昵称
- 🎯 使用 SQLite 持久化存储用户信息
- 💫 优雅的 UI 界面，支持深色/浅色主题

## 技术栈

### 前端
- Vue.js 2.x
- Element UI
- Socket.io-client
- Toast UI Editor (Markdown 编辑器)

### 后端
- Flask
- Flask-SocketIO
- SQLAlchemy
- SQLite

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- npm 7+

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/manxisuo/OnlyChat.git
cd OnlyChat
```

2. 安装后端依赖
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或者
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. 安装前端依赖
```bash
cd ../frontend
npm install
```

### 开发模式运行

1. 启动后端服务器
```bash
cd backend
python app.py
```

2. 启动前端开发服务器
```bash
cd frontend
npm run serve
```

### 生产环境部署

1. 构建前端
```bash
cd frontend
npm run build
```

2. 启动生产服务器
```bash
cd ../backend
python app.py
```

访问 http://localhost:8080 即可使用应用。

## 使用说明

1. 打开应用后，系统会自动使用你的 IP 地址作为初始昵称
2. 点击左上角的昵称标签可以修改你的昵称
3. 在左侧用户列表中选择一个在线用户开始聊天
4. 使用底部输入框发送消息
   - 普通文本模式：直接输入文字
   - Markdown 模式：切换复选框后使用 Markdown 语法
   - 文件发送：点击回形针图标
5. Ctrl + Enter 发送消息，Enter 换行
6. 可以通过左侧和底部的折叠按钮调整界面布局

## 许可证

[MIT License](LICENSE)

## 贡献指南

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 联系方式

如果你有任何问题或建议，欢迎提出 Issue 或 Pull Request。

## 致谢

感谢所有为这个项目做出贡献的开发者。
