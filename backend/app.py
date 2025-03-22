import eventlet
eventlet.monkey_patch()  # 必须在所有其他导入之前执行

from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import time
from models import Session, User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'  # 添加密钥
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='eventlet',
    max_http_buffer_size=1024 * 1024 * 50,  # 增加到50MB
    ping_timeout=60,
    ping_interval=30
)

users = {}
last_heartbeat = {}

DIST_DIR = '../frontend/dist'

def get_real_ip():
    return request.remote_addr

def get_or_create_user(ip):
    session = Session()
    try:
        user = session.query(User).filter_by(ip=ip).first()
        if not user:
            user = User(ip=ip, nickname=ip)
            session.add(user)
            session.commit()
        return user
    finally:
        session.close()

def get_nickname(ip):
    session = Session()
    try:
        user = session.query(User).filter_by(ip=ip).first()
        return user.nickname if user else ip
    finally:
        session.close()

@app.route('/')
def index():
    return send_from_directory(DIST_DIR, 'index.html')

@app.route('/test')
def test():
    client_ip = request.remote_addr
    return f"Your IP address is: {client_ip}"

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(DIST_DIR, path)

@socketio.on('connect')
def handle_connect():
    ip_address = get_real_ip()
    users[ip_address] = request.sid
    last_heartbeat[ip_address] = time.time()
    user = get_or_create_user(ip_address)
    emit('your_ip', {'ip': ip_address, 'nickname': user.nickname})
    emit('user_connected', {'ip': ip_address, 'nickname': user.nickname}, broadcast=True)
    # 发送所有在线用户及其昵称
    online_users = []
    for ip in users.keys():
        online_users.append({
            'ip': ip,
            'nickname': get_nickname(ip)
        })
    emit('update_user_list', online_users, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    ip_address = None
    for ip, sid in users.items():
        if sid == request.sid:
            ip_address = ip
            break
    if ip_address:
        users.pop(ip_address, None)
        last_heartbeat.pop(ip_address, None)
        emit('user_disconnected', ip_address, broadcast=True)
        emit('update_user_list', list(users.keys()), broadcast=True)  # 更新用户列表

@socketio.on('heartbeat')
def handle_heartbeat():
    ip_address = get_real_ip()
    last_heartbeat[ip_address] = time.time()

@socketio.on('send_message')
def handle_send_message(data):
    recipient_ip = data['recipient']
    message = data['message']
    if recipient_ip in users:
        emit('receive_message', {'sender': get_real_ip(), 'message': message}, room=users[recipient_ip])

@socketio.on('send_file_start')
def handle_send_file_start(data):
    recipient_ip = data['recipient']
    file_info = data['fileInfo']
    if recipient_ip in users:
        emit('receive_file_start', {'sender': get_real_ip(), 'fileInfo': file_info}, room=users[recipient_ip])

@socketio.on('send_file_chunk')
def handle_send_file_chunk(data):
    recipient_ip = data['recipient']
    chunk = data['chunk']
    if recipient_ip in users:
        try:
            emit('receive_file_chunk', {
                'sender': get_real_ip(), 
                'chunk': chunk
            }, room=users[recipient_ip])
            # 立即确认接收
            emit('chunk_received', {
                'index': chunk['index'],
                'total': chunk['total']
            })
        except Exception as e:
            print(f"Error forwarding chunk: {str(e)}")
            emit('chunk_error', {
                'index': chunk['index'],
                'error': str(e)
            })

@socketio.on('chunk_ack')
def handle_chunk_ack(data):
    try:
        print(f"Chunk ack received: {data['index']}/{data['total']} for file {data['name']}")
        emit('chunk_received', {
            'index': data['index'],
            'name': data['name']
        })
    except Exception as e:
        print(f"Error handling chunk ack: {e}")
        emit('chunk_error', {
            'index': data['index'],
            'error': str(e)
        })

@socketio.on('update_user_list')
def handle_update_user_list():
    emit('update_user_list', list(users.keys()), broadcast=True)

@socketio.on('file_start')
def handle_file_start(data):
    recipient_ip = data['recipient']
    if recipient_ip in users:
        emit('file_start', {
            'sender': get_real_ip(),
            'fileInfo': data['fileInfo']
        }, room=users[recipient_ip])

@socketio.on('file_data')
def handle_file_data(data):
    recipient_ip = data['recipient']
    if recipient_ip in users:
        emit('file_data', {
            'sender': get_real_ip(),
            'name': data['name'],
            'data': data['data']
        }, room=users[recipient_ip])
        return True  # 确认数据已发送

@socketio.on('file_end')
def handle_file_end(data):
    recipient_ip = data['recipient']
    if recipient_ip in users:
        emit('file_end', {
            'sender': get_real_ip(),
            'name': data['name']
        }, room=users[recipient_ip])

@socketio.on('update_nickname')
def handle_nickname_update(data):
    ip = get_real_ip()
    new_nickname = data['nickname']
    session = Session()
    try:
        user = session.query(User).filter_by(ip=ip).first()
        if user:
            user.nickname = new_nickname
        else:
            user = User(ip=ip, nickname=new_nickname)
            session.add(user)
        session.commit()
        # 广播昵称更新
        emit('nickname_updated', {'ip': ip, 'nickname': new_nickname}, broadcast=True)
    finally:
        session.close()

def check_heartbeat():
    app_context = app.app_context()
    app_context.push()
    
    while True:
        try:
            current_time = time.time()
            disconnected_users = []
            
            for ip, last_time in list(last_heartbeat.items()):
                if current_time - last_time > 6:
                    if ip in users:
                        disconnected_users.append(ip)
            
            for ip in disconnected_users:
                users.pop(ip, None)
                last_heartbeat.pop(ip, None)
                # 修改广播方式
                socketio.emit('user_disconnected', {'ip': ip}, namespace='/')
                socketio.emit('update_user_list', {'users': list(users.keys())}, namespace='/')
            
        except Exception as e:
            print(f"Heartbeat check error: {e}")
        finally:
            eventlet.sleep(1)
    
    app_context.pop()

if __name__ == '__main__':
    eventlet.spawn(check_heartbeat)
    socketio.run(app, host='0.0.0.0', port=8080)
