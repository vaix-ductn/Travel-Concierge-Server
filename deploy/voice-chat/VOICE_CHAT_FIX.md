# Voice Chat Server Fix - Root Cause Analysis & Solution

## 🔍 Root Cause Analysis

### Problem Identified
Flutter app không thể kết nối được với Voice Chat Server trên Google Cloud vì:

1. **Server deployment sai**: Dockerfile đang chạy `test_voice_server.py` (một test server đơn giản) thay vì WebSocket server thực tế
2. **Missing WebSocket implementation**: Test server chỉ có FastAPI endpoints, không có WebSocket server
3. **Configuration mismatch**: Server không được cấu hình đúng cho Cloud Run environment

### Technical Details
- **Current deployed service**: `test_voice_server.py` - chỉ có HTTP endpoints
- **Expected service**: `websocket_server.py` - WebSocket server với Django integration
- **Impact**: Flutter app không thể establish WebSocket connection cho voice chat

## ✅ Solution Implemented

### 1. Created Production Startup Script
- **File**: `deploy/voice-chat/start_voice_server.py`
- **Purpose**: Khởi chạy WebSocket server thực tế với Django integration
- **Features**:
  - Django environment setup
  - WebSocket server initialization
  - Health check HTTP endpoint (port 8080)
  - Proper signal handling
  - Cloud Run compatible configuration

### 2. Updated Dockerfile
- **File**: `deploy/voice-chat/voice-chat.Dockerfile`
- **Changes**:
  - Replaced test server với production startup script
  - Added Django base configuration
  - Updated health check to use HTTP endpoint
  - Exposed both WebSocket port (8003) và health check port (8080)

### 3. Added Required Dependencies
- **File**: `requirements.txt`
- **Added**:
  - `fastapi>=0.104.0` - for health check endpoints
  - `uvicorn>=0.24.0` - for HTTP server

### 4. Created Deployment Script
- **File**: `deploy/voice-chat/deploy_voice_chat.sh`
- **Purpose**: Automated deployment and testing
- **Features**:
  - Builds and deploys to Cloud Run
  - Tests health endpoints
  - Provides WebSocket URL for Flutter app

## 🚀 Deployment Instructions

### Deploy Fixed Voice Chat Server
```bash
cd /workspace
chmod +x deploy/voice-chat/deploy_voice_chat.sh
./deploy/voice-chat/deploy_voice_chat.sh
```

### Manual Deployment
```bash
# Build image
gcloud builds submit --config deploy/voice-chat/voice-chat-cloudbuild.yaml .

# Deploy to Cloud Run
gcloud run deploy voice-chat-server \
    --image us-central1-docker.pkg.dev/travelapp-461806/travel-server-repo/voice-chat-server:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8003 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 5 \
    --timeout 3600
```

## 📱 Flutter App Configuration

### Update WebSocket URL
```dart
// Replace with actual deployed URL
const String voiceChatWebSocketUrl = 'wss://voice-chat-server-277713629269.us-central1.run.app';

// For voice chat connection
final websocket = WebSocketChannel.connect(
  Uri.parse(voiceChatWebSocketUrl),
);
```

### Connection Protocol
```json
{
  "type": "start_session",
  "user_id": "user_123",
  "session_id": "session_456"
}
```

## 🧪 Testing

### Health Check
```bash
curl https://voice-chat-server-277713629269.us-central1.run.app/health/
```

### WebSocket Connection Test
```javascript
const ws = new WebSocket('wss://voice-chat-server-277713629269.us-central1.run.app');
ws.onopen = () => console.log('Connected to voice chat server');
```

## 📊 Monitoring

### View Logs
```bash
gcloud run services logs read voice-chat-server --region us-central1
```

### Service Status
```bash
gcloud run services describe voice-chat-server --region us-central1
```

## 🔧 Architecture

### Before Fix
```
Flutter App → Google Cloud Run → test_voice_server.py (HTTP only)
                                ❌ No WebSocket support
```

### After Fix
```
Flutter App → Google Cloud Run → start_voice_server.py
                                ├── HTTP Health Check (port 8080)
                                └── WebSocket Server (port 8003)
                                    └── Django + ADK Live API
```

## 📋 Next Steps

1. **Deploy the fix**: Run deployment script
2. **Test Flutter connection**: Update Flutter app với WebSocket URL mới
3. **Monitor logs**: Kiểm tra logs để đảm bảo server hoạt động đúng
4. **Performance testing**: Test với multiple concurrent connections

## ⚠️ Important Notes

- WebSocket server chạy trên port 8003
- Health check endpoints trên port 8080
- Server configured để auto-bind 0.0.0.0 cho Cloud Run
- Maximum timeout 3600 seconds (1 hour) cho voice sessions
- Concurrency set to 1000 connections

---

**Created**: Jan 11, 2025  
**Status**: Ready for deployment  
**Priority**: High - Blocking Flutter voice chat functionality