# 📱 Flutter Client cho Travel Concierge API

## 🎯 Tổng quan

Flutter client này tương tác với Travel Concierge Agent thông qua ADK API Server. Nó cung cấp:

- ✅ Chat interface đẹp mắt
- ✅ Real-time streaming response (SSE)
- ✅ Session management tự động
- ✅ Error handling
- ✅ Function response indicators

## 🚀 Cách sử dụng

### 1. Khởi động ADK API Server

Trước tiên, bạn cần khởi động server Python:

```bash
cd D:\DucTN\Source\travel-concierge

# Cài đặt Python dependencies (nếu chưa có)
pip install -r requirements.txt

# Khởi động ADK API server
python -m adk api_server travel_concierge
```

Server sẽ chạy tại `http://127.0.0.1:8000`

### 2. Tạo Flutter Project

```bash
# Tạo Flutter project mới
flutter create travel_concierge_client
cd travel_concierge_client

# Copy files
# - Copy flutter_client_sample.dart -> lib/main.dart
# - Copy pubspec.yaml (đè lên file hiện tại)
```

### 3. Cài đặt dependencies

```bash
flutter pub get
```

### 4. Chạy Flutter app

```bash
flutter run
```

## 📋 API Endpoints được sử dụng

### Tạo Session
```http
POST http://127.0.0.1:8000/apps/travel_concierge/users/{user_id}/sessions/{session_id}
```

### Gửi Message (SSE)
```http
POST http://127.0.0.1:8000/run_sse
Content-Type: application/json
Accept: text/event-stream

{
    "session_id": "session_123",
    "app_name": "travel_concierge",
    "user_id": "user_123",
    "new_message": {
        "role": "user",
        "parts": [
            {"text": "Your prompt here"}
        ]
    }
}
```

## 🎨 Tính năng UI

### Chat Interface
- **User messages**: Màu xanh, hiển thị bên phải
- **Agent messages**: Màu xám, hiển thị bên trái với tên agent
- **System messages**: Màu xám nhạt với icon info
- **Timestamps**: Hiển thị thời gian gửi message

### Loading States
- Hiển thị indicator khi agent đang xử lý
- Disable input khi đang loading
- Auto-scroll xuống message mới

### Function Response Indicators
- 🏝️ Place suggestions
- 📍 Activities/POI
- ✈️ Flight options
- 🏨 Hotel options
- 📅 Itinerary generated

## 🔧 Cấu hình

### Thay đổi Server URL
Trong file `flutter_client_sample.dart`, tìm:

```dart
static const String BASE_URL = 'http://127.0.0.1:8000';
```

Thay đổi thành server URL của bạn.

### Custom User ID/Session ID
Mặc định app sẽ tạo user_id và session_id tự động dựa trên timestamp.
Bạn có thể custom trong method `_generateSessionInfo()`.

## 📱 Sample Usage

### Ví dụ các câu hỏi hay:

1. **Destination Inspiration:**
   ```
   "Inspire me about destinations in Southeast Asia"
   ```

2. **Activity Planning:**
   ```
   "Show me activities in Bali for 3 days"
   ```

3. **Flight Search:**
   ```
   "Find flights from Ho Chi Minh City to Bangkok on March 15th"
   ```

4. **Complete Trip Planning:**
   ```
   "Plan a 5-day trip to Thailand from Vietnam, including flights and hotels"
   ```

## 🐛 Troubleshooting

### Common Issues:

1. **"Failed to create session"**
   - Đảm bảo ADK server đang chạy tại port 8000
   - Check server logs

2. **"Network error"**
   - Kiểm tra kết nối internet
   - Đảm bảo firewall không block port 8000

3. **"Agent Error"**
   - Thường do function call lỗi
   - Check server logs để debug

## 🔧 Customization

### Thêm Rich UI cho Function Responses

Trong method `_handleFunctionResponse()`, bạn có thể thêm:

```dart
case 'place_agent':
  // Parse response và hiển thị carousel destinations
  final places = response['places'] as List;
  _showDestinationCarousel(places);
  break;

case 'itinerary_agent':
  // Parse response và hiển thị itinerary timeline
  final itinerary = response['itinerary'];
  _showItineraryView(itinerary);
  break;
```

### Custom Message Types

Bạn có thể extend `ChatMessage` class để support:
- Image messages
- Card/carousel messages
- Action buttons
- Maps/location

## 🌟 Next Steps

1. **Rich Media Support**: Thêm support cho images, maps
2. **Offline Mode**: Cache conversations
3. **Push Notifications**: Thông báo khi có update
4. **Voice Input**: Speech-to-text integration
5. **Multiple Sessions**: Quản lý nhiều trip cùng lúc

## 📞 Support

Nếu có vấn đề, check:
1. Server logs: `adk api_server travel_concierge --verbose`
2. Flutter logs: `flutter logs`
3. Network inspection: DevTools network tab