# 🤖 AI Agent API Testing Guide

## 📋 **Available API Endpoints**

### 🔗 **Base URL**: `http://localhost:8000/api/`

---

## 🤖 **AI Agent Endpoints**

### 1. **Chat with Agent**
**Endpoint**: `POST /api/agent/chat/`

**Purpose**: Gửi tin nhắn chat đến AI Agent

**Request Body**:
```json
{
    "message": "I want to travel to Japan for 7 days",
    "user_id": "user123",
    "session_id": "session456"  // Optional
}
```

**Response**:
```json
{
    "success": true,
    "data": {
        "success": true,
        "response": "Agent response to: I want to travel to Japan for 7 days",
        "user_id": "user123",
        "session_id": "session456"
    }
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/agent/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to travel to Japan for 7 days",
    "user_id": "user123"
  }'
```

---

### 2. **Get Agent Status**
**Endpoint**: `GET /api/agent/status/`

**Purpose**: Lấy thông tin trạng thái của AI Agent system

**Query Parameters**:
- `include_sub_agents=true` (default: true)
- `include_tools_status=false` (default: false)
- `detailed_info=false` (default: false)

**Response**:
```json
{
    "success": true,
    "data": {
        "agent_name": "root_agent",
        "description": "A Travel Conceirge using the services of multiple sub-agents",
        "sub_agents_count": 6,
        "status": "active",
        "sub_agents": [
            {
                "name": "inspiration_agent",
                "description": "Agent for travel inspiration"
            },
            {
                "name": "planning_agent",
                "description": "Agent for travel planning"
            }
        ]
    }
}
```

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/agent/status/?include_sub_agents=true&include_tools_status=true"
```

---

### 3. **List Sub-Agents**
**Endpoint**: `GET /api/agent/sub-agents/`

**Purpose**: Lấy danh sách tất cả sub-agents có sẵn

**Response**:
```json
{
    "success": true,
    "data": {
        "sub_agents": [
            {
                "name": "inspiration_agent",
                "description": "Agent for travel inspiration"
            },
            {
                "name": "planning_agent",
                "description": "Agent for travel planning"
            },
            {
                "name": "booking_agent",
                "description": "Agent for travel booking"
            },
            {
                "name": "pre_trip_agent",
                "description": "Agent for pre-trip preparation"
            },
            {
                "name": "in_trip_agent",
                "description": "Agent for in-trip assistance"
            },
            {
                "name": "post_trip_agent",
                "description": "Agent for post-trip activities"
            }
        ],
        "count": 6
    }
}
```

**cURL Example**:
```bash
curl -X GET http://localhost:8000/api/agent/sub-agents/
```

---

### 4. **Agent Interaction**
**Endpoint**: `POST /api/agent/interaction/`

**Purpose**: Complex agent interactions với specific parameters

**Request Body**:
```json
{
    "interaction_type": "planning",
    "parameters": {
        "destination": "Tokyo",
        "duration": 7,
        "budget": "mid-range"
    },
    "user_context": {
        "preferences": ["culture", "food"],
        "group_size": 2
    }
}
```

**Valid interaction_types**: `chat`, `recommendation`, `planning`, `booking`, `inspiration`, `pre_trip`, `in_trip`, `post_trip`

**Response**:
```json
{
    "success": true,
    "data": {
        "interaction_type": "planning",
        "processed": true,
        "parameters_received": {
            "destination": "Tokyo",
            "duration": 7,
            "budget": "mid-range"
        },
        "user_context_received": {
            "preferences": ["culture", "food"],
            "group_size": 2
        },
        "message": "Processed planning interaction"
    }
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/agent/interaction/ \
  -H "Content-Type: application/json" \
  -d '{
    "interaction_type": "planning",
    "parameters": {
        "destination": "Tokyo",
        "duration": 7
    }
  }'
```

---

## 🧳 **Travel Service Endpoints**

### 5. **Get Travel Recommendations**
**Endpoint**: `POST /api/recommendations/`

**Purpose**: Lấy travel recommendations dựa trên preferences

**Request Body**:
```json
{
    "destination_type": "beach",
    "budget_range": "mid-range",
    "travel_dates": "Summer 2024",
    "group_size": 2,
    "interests": ["relaxation", "culture"],
    "special_requirements": "Accessible accommodations"
}
```

**Valid destination_types**: `beach`, `mountain`, `city`, `countryside`, `adventure`, `cultural`, `relaxation`, `business`, `family`, `romantic`

**Valid budget_ranges**: `budget`, `mid-range`, `luxury`, `ultra-luxury`

**Response**:
```json
{
    "success": true,
    "data": {
        "success": true,
        "recommendations": [
            {
                "destination": "Sample Destination",
                "type": "beach",
                "budget_match": "mid-range",
                "description": "Sample travel recommendation"
            }
        ],
        "preferences_used": {
            "destination_type": "beach",
            "budget_range": "mid-range"
        }
    }
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/recommendations/ \
  -H "Content-Type: application/json" \
  -d '{
    "destination_type": "beach",
    "budget_range": "mid-range",
    "group_size": 2
  }'
```

---

### 6. **Tools Status**
**Endpoint**: `GET /api/tools/status/`

**Purpose**: Kiểm tra status của travel tools (Places API, Search, Memory)

**Response**:
```json
{
    "success": true,
    "data": {
        "overall_status": "healthy",
        "tools": {
            "places_api": {
                "healthy": true,
                "service": "Google Places API",
                "status": "available"
            },
            "search_tools": {
                "healthy": true,
                "service": "Search Tools",
                "status": "available"
            },
            "memory_tools": {
                "healthy": true,
                "service": "Memory Tools",
                "status": "available"
            }
        }
    }
}
```

**cURL Example**:
```bash
curl -X GET http://localhost:8000/api/tools/status/
```

---

### 7. **Health Check**
**Endpoint**: `GET /api/health/`

**Purpose**: Simple health check cho toàn bộ system

**Response**:
```json
{
    "success": true,
    "status": "healthy",
    "timestamp": null,
    "services": {
        "travel_service": "operational",
        "tools": "healthy"
    }
}
```

**cURL Example**:
```bash
curl -X GET http://localhost:8000/api/health/
```

---

## 🚀 **Getting Started**

### 1. **Start Django Server**
```bash
cd travel-concierge
python manage.py runserver
```

### 2. **Test Basic Health Check**
```bash
curl -X GET http://localhost:8000/api/health/
```

### 3. **Test Agent Status**
```bash
curl -X GET http://localhost:8000/api/agent/status/
```

### 4. **Test Chat with Agent**
```bash
curl -X POST http://localhost:8000/api/agent/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I need help planning a trip to Tokyo",
    "user_id": "test_user_001"
  }'
```

---

## 📱 **Testing Tools**

### **Using Postman**
1. Import the endpoints above
2. Set base URL: `http://localhost:8000`
3. Add headers: `Content-Type: application/json`
4. Test each endpoint with sample payloads

### **Using Python Requests**
```python
import requests

# Test agent status
response = requests.get('http://localhost:8000/api/agent/status/')
print(response.json())

# Test chat
chat_data = {
    "message": "I want to visit Japan",
    "user_id": "python_test_user"
}
response = requests.post('http://localhost:8000/api/agent/chat/', json=chat_data)
print(response.json())
```

### **Using JavaScript/Fetch**
```javascript
// Test agent status
fetch('http://localhost:8000/api/agent/status/')
  .then(response => response.json())
  .then(data => console.log(data));

// Test chat
fetch('http://localhost:8000/api/agent/chat/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'I want to travel to Tokyo',
    user_id: 'js_test_user'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## ⚠️ **Error Handling**

### **Common Error Responses**

**400 Bad Request** - Validation Error:
```json
{
    "success": false,
    "error": "Message cannot be empty"
}
```

**500 Internal Server Error** - Server Error:
```json
{
    "success": false,
    "error": "Unable to process chat message"
}
```

---

## 🔧 **Environment Setup**

### **Required Environment Variables**
```bash
# .env file
GOOGLE_CLOUD_API_KEY=your-api-key-here
GOOGLE_PLACES_API_KEY=your-places-api-key
TRAVEL_CONCIERGE_SCENARIO=travel_concierge/profiles/itinerary_empty_default.json
```

### **Django Settings**
Ensure these apps are in `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ...
    'travel_concierge',
    'user_manager',
    'rest_framework',
]
```

---

## 📚 **Next Steps**

1. **Test all endpoints** với sample data
2. **Integrate với frontend** application
3. **Add authentication** nếu cần thiết
4. **Monitor logs** trong `logs/` folder
5. **Scale up** cho production environment

**Happy Testing! 🎉**