/**
 * Travel Concierge Voice Chat Test Client
 * Web interface for testing voice chat functionality
 */

class VoiceChatTestClient {
    constructor() {
        this.websocket = null;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.audioContext = null;
        this.isRecording = false;
        this.isConnected = false;
        this.sessionId = null;
        
        // Audio settings
        this.sampleRate = 16000;
        this.audioFormat = 'audio/pcm';
        
        // Debug logging
        this.debugEnabled = false;
        this.logHistory = [];
        this.maxLogHistory = 100;
        
        // UI elements
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusText = document.getElementById('statusText');
        this.serverUrl = document.getElementById('serverUrl');
        this.sessionIdDisplay = document.getElementById('sessionId');
        this.chatArea = document.getElementById('chatArea');
        this.visualizer = document.getElementById('visualizer');
        
        // Controls
        this.connectBtn = document.getElementById('connectBtn');
        this.disconnectBtn = document.getElementById('disconnectBtn');
        this.recordBtn = document.getElementById('recordBtn');
        this.stopBtn = document.getElementById('stopBtn');
        
        // Settings
        this.serverUrlInput = document.getElementById('serverUrlInput');
        this.clientIdInput = document.getElementById('clientIdInput');
        this.modeSelect = document.getElementById('modeSelect');
        this.autoReconnect = document.getElementById('autoReconnect');
        this.debugMode = document.getElementById('debugMode');
        
        // Test mode flag
        this.testMode = false;
        
        // Message deduplication
        this.lastTranscript = '';
        this.messageHistory = new Set();
        
        this.setupEventListeners();
        this.updateWelcomeTime();
        this.setupAudioVisualization();
        this.setupDebugLogging();
    }
    
    setupDebugLogging() {
        // Enable debug mode from checkbox
        this.debugMode.addEventListener('change', (e) => {
            this.debugEnabled = e.target.checked;
            if (this.debugEnabled) {
                this.log('🐛 Debug mode enabled');
                this.addMessage('Debug mode được bật', 'system');
            } else {
                this.log('🐛 Debug mode disabled');
                this.addMessage('Debug mode được tắt', 'system');
            }
        });
        
        // Add log display area
        this.createLogDisplay();
    }
    
    createLogDisplay() {
        const logContainer = document.createElement('div');
        logContainer.innerHTML = `
            <div class="settings" style="margin-top: 10px;">
                <h3>📋 Debug Logs</h3>
                <div id="debugLogs" style="
                    background: #f8f9fa;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    max-height: 200px;
                    overflow-y: auto;
                    font-family: monospace;
                    font-size: 12px;
                    line-height: 1.4;
                "></div>
                <div style="margin-top: 10px; margin-bottom: 10px;">
                    <label style="font-weight: 500; margin-right: 10px;">Filter:</label>
                    <select id="logFilter" style="padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px;">
                        <option value="all">All Logs</option>
                        <option value="ERROR">Errors Only</option>
                        <option value="WARN">Warnings & Errors</option>
                        <option value="INFO">Info & Above</option>
                    </select>
                </div>
                <div class="log-buttons">
                    <button id="clearLogs" class="btn btn-clear">🧹 Clear Logs</button>
                    <button id="copyLogs" class="btn btn-copy">📋 Copy Logs</button>
                    <button id="downloadLogs" class="btn btn-download">💾 Download</button>
                </div>
            </div>
        `;
        
        document.querySelector('.container').appendChild(logContainer);
        
        this.debugLogsContainer = document.getElementById('debugLogs');
        
        document.getElementById('clearLogs').addEventListener('click', () => {
            this.clearLogs();
        });
        
        document.getElementById('copyLogs').addEventListener('click', () => {
            this.copyLogs();
        });
        
        document.getElementById('downloadLogs').addEventListener('click', () => {
            this.downloadLogs();
        });
        
        document.getElementById('logFilter').addEventListener('change', (e) => {
            this.filterLogs(e.target.value);
        });
    }
    
    log(message, level = 'INFO') {
        const timestamp = new Date().toLocaleTimeString('vi-VN', { 
            hour12: false,
            hour: '2-digit',
            minute: '2-digit', 
            second: '2-digit',
            fractionalSecondDigits: 3
        });
        
        const logEntry = {
            timestamp,
            level,
            message,
            fullMessage: `[${timestamp}] ${level}: ${message}`
        };
        
        // Add to history
        this.logHistory.push(logEntry);
        if (this.logHistory.length > this.maxLogHistory) {
            this.logHistory.shift();
        }
        
        // Always log to console
        const consoleMethod = level === 'ERROR' ? 'error' : level === 'WARN' ? 'warn' : 'log';
        console[consoleMethod](`[VoiceChat] ${logEntry.fullMessage}`);
        
        // Show in debug container if debug mode enabled
        if (this.debugEnabled && this.debugLogsContainer) {
            const logDiv = document.createElement('div');
            logDiv.style.color = level === 'ERROR' ? '#dc3545' : level === 'WARN' ? '#ffc107' : '#333';
            logDiv.textContent = logEntry.fullMessage;
            
            this.debugLogsContainer.appendChild(logDiv);
            this.debugLogsContainer.scrollTop = this.debugLogsContainer.scrollHeight;
        }
    }
    
    clearLogs() {
        this.logHistory = [];
        if (this.debugLogsContainer) {
            this.debugLogsContainer.innerHTML = '';
        }
        this.log('🧹 Logs cleared');
    }
    
    async copyLogs() {
        try {
            const logsText = this.formatLogsForExport();
            
            if (navigator.clipboard && window.isSecureContext) {
                // Use modern clipboard API
                await navigator.clipboard.writeText(logsText);
                this.showSuccess('📋 Logs copied to clipboard!');
                this.log('✅ Logs copied to clipboard successfully');
            } else {
                // Fallback for older browsers
                this.fallbackCopyToClipboard(logsText);
            }
        } catch (error) {
            this.log(`❌ Failed to copy logs: ${error.message}`, 'ERROR');
            this.showError('Không thể copy logs');
        }
    }
    
    fallbackCopyToClipboard(text) {
        // Create temporary textarea element
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        
        try {
            textArea.focus();
            textArea.select();
            const successful = document.execCommand('copy');
            
            if (successful) {
                this.showSuccess('📋 Logs copied to clipboard!');
                this.log('✅ Logs copied to clipboard (fallback method)');
            } else {
                throw new Error('Copy command failed');
            }
        } catch (error) {
            this.log(`❌ Fallback copy failed: ${error.message}`, 'ERROR');
            this.showError('Không thể copy logs');
        } finally {
            document.body.removeChild(textArea);
        }
    }
    
    downloadLogs() {
        try {
            const logsText = this.formatLogsForExport();
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `voice-chat-logs-${timestamp}.txt`;
            
            // Create blob and download link
            const blob = new Blob([logsText], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.style.display = 'none';
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            // Clean up the URL object
            window.URL.revokeObjectURL(url);
            
            this.showSuccess(`💾 Logs downloaded as ${filename}`);
            this.log(`✅ Logs downloaded as ${filename}`);
            
        } catch (error) {
            this.log(`❌ Failed to download logs: ${error.message}`, 'ERROR');
            this.showError('Không thể download logs');
        }
    }
    
    formatLogsForExport() {
        const header = `=== Voice Chat Debug Logs ===
Generated: ${new Date().toLocaleString('vi-VN')}
URL: ${window.location.href}
User Agent: ${navigator.userAgent}
Total Log Entries: ${this.logHistory.length}

`;
        
        const logsText = this.logHistory
            .map(entry => entry.fullMessage)
            .join('\n');
        
        const footer = `

=== End of Logs ===`;
        
        return header + logsText + footer;
    }
    
    filterLogs(filterLevel) {
        if (!this.debugLogsContainer) return;
        
        this.log(`🔍 Filtering logs by level: ${filterLevel}`);
        
        // Clear current display
        this.debugLogsContainer.innerHTML = '';
        
        // Filter logs based on level
        const filteredLogs = this.logHistory.filter(entry => {
            if (filterLevel === 'all') return true;
            if (filterLevel === 'ERROR') return entry.level === 'ERROR';
            if (filterLevel === 'WARN') return entry.level === 'ERROR' || entry.level === 'WARN';
            if (filterLevel === 'INFO') return true; // INFO includes all levels
            return true;
        });
        
        // Display filtered logs
        filteredLogs.forEach(entry => {
            const logDiv = document.createElement('div');
            logDiv.style.color = entry.level === 'ERROR' ? '#dc3545' : 
                                entry.level === 'WARN' ? '#ffc107' : '#333';
            logDiv.textContent = entry.fullMessage;
            this.debugLogsContainer.appendChild(logDiv);
        });
        
        this.debugLogsContainer.scrollTop = this.debugLogsContainer.scrollHeight;
        this.log(`✅ Showing ${filteredLogs.length} of ${this.logHistory.length} logs`);
    }
    
    // Removed shouldSkipTranscript - server-side buffering handles deduplication
    
    updateUrl() {
        const mode = this.modeSelect.value;
        const clientId = this.clientIdInput.value;
        
        // Use test_ prefix for test mode, regular client id for voice mode
        const finalClientId = mode === 'test' ? 
            (clientId.startsWith('test_') ? clientId : 'test_' + clientId) :
            clientId.replace(/^test_/, '');
        
        const baseUrl = 'ws://localhost:8003/ws/';
        const newUrl = baseUrl + finalClientId;
        
        this.serverUrlInput.value = newUrl;
        this.serverUrl.textContent = newUrl;
        this.clientIdInput.value = finalClientId;
        
        this.log(`🔄 Updated URL: ${newUrl} (mode: ${mode})`);
    }
    
    setupEventListeners() {
        this.connectBtn.addEventListener('click', () => this.connect());
        this.disconnectBtn.addEventListener('click', () => this.disconnect());
        this.recordBtn.addEventListener('click', () => this.startRecording());
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        
        // Settings change handlers
        this.serverUrlInput.addEventListener('change', (e) => {
            this.serverUrl.textContent = e.target.value;
        });
        
        this.clientIdInput.addEventListener('change', (e) => {
            this.updateUrl();
        });
        
        this.modeSelect.addEventListener('change', (e) => {
            this.updateUrl();
            this.log(`🔄 Mode changed to: ${e.target.value}`);
        });
        
        this.debugMode.addEventListener('change', (e) => {
            if (e.target.checked) {
                console.log('Debug mode enabled');
            }
        });
    }
    
    updateWelcomeTime() {
        const welcomeTime = document.getElementById('welcomeTime');
        if (welcomeTime) {
            welcomeTime.textContent = new Date().toLocaleTimeString('vi-VN');
        }
    }
    
    setupAudioVisualization() {
        const bars = this.visualizer.querySelectorAll('.wave-bar');
        
        // Animate bars when not recording
        this.visualizerInterval = setInterval(() => {
            if (!this.isRecording) {
                bars.forEach(bar => {
                    const height = Math.random() * 40 + 10;
                    bar.style.height = height + 'px';
                });
            }
        }, 200);
    }
    
    updateStatus(status, className = '') {
        this.statusText.textContent = status;
        this.statusIndicator.className = `status-indicator ${className}`;
        
        if (this.debugMode.checked) {
            console.log(`Status: ${status}`);
        }
    }
    
    updateControls() {
        this.connectBtn.disabled = this.isConnected;
        this.disconnectBtn.disabled = !this.isConnected;
        this.recordBtn.disabled = !this.isConnected || this.isRecording;
        this.stopBtn.disabled = !this.isRecording;
    }
    
    addMessage(content, type = 'system', timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.textContent = content;
        messageDiv.appendChild(contentDiv);
        
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'timestamp';
        timestampDiv.textContent = timestamp || new Date().toLocaleTimeString('vi-VN');
        messageDiv.appendChild(timestampDiv);
        
        this.chatArea.appendChild(messageDiv);
        this.chatArea.scrollTop = this.chatArea.scrollHeight;
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.textContent = `❌ Lỗi: ${message}`;
        this.chatArea.appendChild(errorDiv);
        this.chatArea.scrollTop = this.chatArea.scrollHeight;
        
        // Auto remove after 10 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 10000);
    }
    
    showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success';
        successDiv.textContent = `✅ ${message}`;
        this.chatArea.appendChild(successDiv);
        this.chatArea.scrollTop = this.chatArea.scrollHeight;
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        }, 5000);
    }
    
    async connect() {
        try {
            this.log('🔌 Starting WebSocket connection...');
            this.updateStatus('Đang kết nối...', 'status-connecting');
            
            const url = this.serverUrlInput.value;
            this.log(`📍 Connecting to URL: ${url}`);
            this.log('🔧 WebSocket protocols: none (testing without subprotocol)');
            
            // Try without subprotocol first to see if that's the issue
            this.websocket = new WebSocket(url);
            this.log('🚀 WebSocket object created');
            
            this.websocket.onopen = (event) => {
                this.log('✅ WebSocket onopen event triggered');
                this.log(`📊 WebSocket readyState: ${this.websocket.readyState}`);
                this.log(`🌐 WebSocket URL: ${this.websocket.url}`);
                this.log(`🔌 WebSocket protocol: ${this.websocket.protocol}`);
                
                this.isConnected = true;
                this.updateStatus('Đã kết nối', 'status-connected');
                this.updateControls();
                this.addMessage('Kết nối WebSocket thành công!', 'system');
                this.showSuccess('Kết nối thành công đến voice server');
                this.log('🎉 Connection established successfully');
            };
            
            this.websocket.onmessage = (event) => {
                this.log(`📥 Received message: ${event.data.length > 100 ? event.data.substring(0, 100) + '...' : event.data}`);
                this.handleServerMessage(event.data);
            };
            
            this.websocket.onclose = (event) => {
                this.log(`🔌 WebSocket onclose event: code=${event.code}, reason="${event.reason}", wasClean=${event.wasClean}`);
                
                this.isConnected = false;
                this.updateStatus('Đã ngắt kết nối', 'status-disconnected');
                this.updateControls();
                this.addMessage(`Kết nối WebSocket đã đóng (code: ${event.code})`, 'system');
                
                if (event.code !== 1000) {
                    this.log(`⚠️ Abnormal closure: ${event.code} - ${event.reason}`, 'WARN');
                }
                
                if (this.autoReconnect.checked && event.code !== 1000) {
                    this.log('🔄 Auto-reconnect enabled, retrying in 3 seconds...');
                    setTimeout(() => this.connect(), 3000);
                }
            };
            
            this.websocket.onerror = (error) => {
                this.log(`❌ WebSocket error occurred`, 'ERROR');
                this.log(`📍 Error details: ${JSON.stringify(error)}`, 'ERROR');
                console.error('WebSocket error:', error);
                this.showError('Lỗi kết nối WebSocket');
                this.updateStatus('Lỗi kết nối', 'status-disconnected');
                this.updateControls();
            };
            
        } catch (error) {
            this.log(`💥 Connection exception: ${error.message}`, 'ERROR');
            this.log(`📍 Stack trace: ${error.stack}`, 'ERROR');
            console.error('Connection error:', error);
            this.showError(`Không thể kết nối: ${error.message}`);
            this.updateStatus('Lỗi kết nối', 'status-disconnected');
            this.updateControls();
        }
    }
    
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
        }
        
        if (this.isRecording) {
            this.stopRecording();
        }
        
        this.isConnected = false;
        this.sessionId = null;
        this.sessionIdDisplay.textContent = '-';
        this.updateStatus('Chưa kết nối', 'status-disconnected');
        this.updateControls();
        this.addMessage('Đã ngắt kết nối thủ công', 'system');
    }
    
    handleServerMessage(data) {
        try {
            this.log(`🔍 Parsing server message: ${data.substring(0, 200)}${data.length > 200 ? '...' : ''}`);
            const message = JSON.parse(data);
            
            this.log(`📨 Message type: ${message.type}`);
            this.log(`📄 Message data: ${JSON.stringify(message.data).substring(0, 100)}${JSON.stringify(message.data).length > 100 ? '...' : ''}`);
            
            switch (message.type) {
                case 'connected':
                    this.log(`✅ Connection confirmed: ${message.data.message}`);
                    this.sessionId = message.data.session_id;
                    this.sessionIdDisplay.textContent = this.sessionId;
                    this.addMessage(`Kết nối thành công! Session: ${this.sessionId}`, 'system');
                    break;
                    
                case 'test_echo':
                    this.log(`🔄 Test echo received: ${message.data.message}`);
                    this.addMessage(`Echo: ${message.data.message}`, 'system');
                    this.testMode = true;
                    break;
                    
                case 'transcript':
                    const transcript = message.data.trim();
                    this.log(`💬 Received transcript: ${transcript}`);
                    
                    // Server-side buffering handles deduplication, but keep basic checks
                    if (transcript.length < 2) {
                        this.log(`⏭️ Skipping very short transcript`);
                        break;
                    }
                    
                    // Only skip exact duplicates (server handles streaming chunks)
                    if (transcript === this.lastTranscript) {
                        this.log(`🔄 Skipping exact duplicate transcript`);
                        break;
                    }
                    
                    this.addMessage(transcript, 'ai');
                    this.lastTranscript = transcript;
                    this.messageHistory.add(transcript);
                    break;
                    
                case 'audio_chunk':
                    this.log(`🔊 Received audio chunk: ${message.data.length} characters (base64)`);
                    this.handleAudioChunk(message.data);
                    break;
                    
                case 'turn_complete':
                    this.log('✅ Turn complete received');
                    this.addMessage('AI đã hoàn thành phản hồi', 'system');
                    this.updateStatus('Đã kết nối', 'status-connected');
                    break;
                    
                case 'interrupted':
                    this.log('⚠️ Conversation interrupted');
                    this.addMessage('Cuộc trò chuyện bị ngắt', 'system');
                    break;
                    
                case 'error':
                    const errorMsg = message.data?.error_message || message.message || 'Unknown error';
                    this.log(`❌ Server error: ${errorMsg}`, 'ERROR');
                    this.showError(errorMsg);
                    break;
                    
                default:
                    this.log(`❓ Unknown message type: ${message.type}`, 'WARN');
                    this.log(`📄 Full message: ${JSON.stringify(message)}`, 'WARN');
            }
            
        } catch (error) {
            this.log(`💥 Error parsing server message: ${error.message}`, 'ERROR');
            this.log(`📍 Raw data: ${data}`, 'ERROR');
            console.error('Error parsing server message:', error);
            this.showError('Lỗi phân tích tin nhắn từ server');
        }
    }
    
    handleAudioChunk(base64Data) {
        try {
            // Decode base64 audio data
            const audioData = atob(base64Data);
            const audioArray = new Uint8Array(audioData.length);
            
            for (let i = 0; i < audioData.length; i++) {
                audioArray[i] = audioData.charCodeAt(i);
            }
            
            // Play audio (simplified - in real implementation would need proper audio handling)
            this.addMessage('🔊 Nhận được âm thanh từ AI (' + audioArray.length + ' bytes)', 'system');
            this.updateStatus('AI đang phản hồi', 'status-playing');
            
            // Simulate playing time
            setTimeout(() => {
                if (this.isConnected) {
                    this.updateStatus('Đã kết nối', 'status-connected');
                }
            }, 2000);
            
        } catch (error) {
            console.error('Error handling audio chunk:', error);
            this.showError('Lỗi xử lý âm thanh từ server');
        }
    }
    
    async startRecording() {
        try {
            this.log('🎙️ Starting recording...');
            this.log(`🔧 Audio settings: sampleRate=${this.sampleRate}, channelCount=1, echoCancellation=true, noiseSuppression=true`);
            
            // Request microphone permission
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: this.sampleRate,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            
            this.log('✅ Microphone access granted');
            this.log(`🎤 Audio stream tracks: ${this.audioStream.getTracks().length}`);
            
            this.setupAudioRecording();
            this.isRecording = true;
            this.updateStatus('Đang ghi âm', 'status-recording');
            this.updateControls();
            this.addMessage('🎙️ Bắt đầu ghi âm...', 'user');
            this.showSuccess('Đã bắt đầu ghi âm');
            
            // Add recording visual effect
            this.recordBtn.classList.add('recording');
            this.log('🎉 Recording started successfully');
            
        } catch (error) {
            this.log(`❌ Recording error: ${error.message}`, 'ERROR');
            this.log(`📍 Error name: ${error.name}`, 'ERROR');
            console.error('Error starting recording:', error);
            this.showError(`Không thể bắt đầu ghi âm: ${error.message}`);
        }
    }
    
    setupAudioRecording() {
        this.log('🔊 Setting up audio recording...');
        
        // Create audio context for processing
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: this.sampleRate
        });
        
        this.log(`🎵 Audio context created: sampleRate=${this.audioContext.sampleRate}, state=${this.audioContext.state}`);
        
        const source = this.audioContext.createMediaStreamSource(this.audioStream);
        this.log('🎤 Media stream source created');
        
        // Choose audio source based on mode
        if (this.testMode || this.modeSelect.value === 'test') {
            this.log('🧪 Test mode: Using dummy audio data');
            this.setupDummyAudioSending();
        } else {
            this.log('🎙️ Voice mode: Using real microphone audio');
            this.setupRealAudioRecording(source);
        }
        
        this.log('✅ Audio recording setup complete');
    }
    
    setupDummyAudioSending() {
        // Simple approach: send dummy audio chunks periodically for testing
        this.log('⏰ Setting up 500ms interval for sending dummy audio chunks');
        this.recordingInterval = setInterval(() => {
            if (this.isRecording && this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                // Generate dummy audio data for testing
                const dummyAudioData = this.generateTestAudio();
                this.websocket.send(dummyAudioData);
                
                this.log(`📤 Sent dummy audio chunk: ${dummyAudioData.byteLength} bytes`);
            } else {
                this.log(`⚠️ Skip sending: recording=${this.isRecording}, websocket=${!!this.websocket}, readyState=${this.websocket?.readyState}`, 'WARN');
            }
        }, 500); // Send every 500ms
    }
    
    setupRealAudioRecording(source) {
        // Set up real microphone audio processing
        this.log('🎤 Setting up real microphone audio processing');
        
        try {
            // Create a script processor for capturing audio data
            const bufferSize = 4096; // Buffer size
            const scriptProcessor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);
            
            source.connect(scriptProcessor);
            scriptProcessor.connect(this.audioContext.destination);
            
            scriptProcessor.onaudioprocess = (event) => {
                if (this.isRecording && this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                    const inputBuffer = event.inputBuffer;
                    const inputData = inputBuffer.getChannelData(0);
                    
                    // Convert float32 audio data to PCM 16-bit
                    const pcmData = this.convertToPCM16(inputData);
                    this.websocket.send(pcmData);
                    
                    this.log(`📤 Sent real audio chunk: ${pcmData.byteLength} bytes`);
                }
            };
            
            this.scriptProcessor = scriptProcessor;
            this.log('✅ Real audio recording setup complete');
            
        } catch (error) {
            this.log(`❌ Failed to setup real audio recording: ${error.message}`, 'ERROR');
            // Fallback to dummy audio
            this.log('🔄 Falling back to dummy audio', 'WARN');
            this.setupDummyAudioSending();
        }
    }
    
    convertToPCM16(float32Array) {
        // Convert Float32Array to PCM 16-bit
        const buffer = new ArrayBuffer(float32Array.length * 2);
        const view = new DataView(buffer);
        
        for (let i = 0; i < float32Array.length; i++) {
            // Convert float (-1.0 to 1.0) to 16-bit signed integer
            const sample = Math.max(-1, Math.min(1, float32Array[i]));
            const intSample = sample * 0x7FFF;
            view.setInt16(i * 2, intSample, true); // little endian
        }
        
        return buffer;
    }
    
    generateTestAudio() {
        // Generate simple PCM test audio (sine wave)
        const duration = 0.5; // 0.5 seconds
        const samples = this.sampleRate * duration;
        const buffer = new ArrayBuffer(samples * 2); // 16-bit = 2 bytes per sample
        const view = new DataView(buffer);
        
        const frequency = 440; // A4 note
        for (let i = 0; i < samples; i++) {
            const t = i / this.sampleRate;
            const sample = Math.sin(2 * Math.PI * frequency * t) * 0.3; // Reduced amplitude
            const intSample = Math.max(-32767, Math.min(32767, sample * 32767));
            view.setInt16(i * 2, intSample, true); // Little endian
        }
        
        return buffer;
    }
    
    stopRecording() {
        this.isRecording = false;
        
        if (this.recordingInterval) {
            clearInterval(this.recordingInterval);
            this.recordingInterval = null;
        }
        
        if (this.scriptProcessor) {
            this.scriptProcessor.disconnect();
            this.scriptProcessor = null;
        }
        
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }
        
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        
        this.updateStatus('Đã kết nối', 'status-connected');
        this.updateControls();
        this.addMessage('⏹️ Đã dừng ghi âm', 'user');
        this.recordBtn.classList.remove('recording');
    }
}

// Initialize the client when page loads
let voiceChatClient = null;

document.addEventListener('DOMContentLoaded', () => {
    voiceChatClient = new VoiceChatTestClient();
    console.log('Voice Chat Test Client initialized');
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (voiceChatClient) {
        voiceChatClient.disconnect();
    }
});