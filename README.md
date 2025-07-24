# 🚀 Travel Concierge - Django Backend Server

## 📋 Tổng quan

Travel Concierge là một ứng dụng du lịch thông minh với AI Agent tích hợp, cung cấp:
- **REST API Backend** với Django
- **AI Agent** cho travel planning và assistance
- **Authentication System** với JWT
- **User Management** với profiles
- **Travel Services** với recommendations

## 🏗️ Kiến trúc

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flutter App   │    │   Django API    │    │   ADK Agent     │
│                 │◄──►│   Server        │◄──►│   Server        │
│   (Mobile)      │    │   (Cloud Run)   │    │   (Cloud Run)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────────────────────────────┐
                       │           Cloud SQL                    │
                       │         (MySQL Database)               │
                       └─────────────────────────────────────────┘
```

## 📁 Cấu trúc thư mục

```
Server/travel_server/
├── config/                     # Django settings
├── travel_concierge/           # Main Django app với AI agents
├── user_manager/               # User authentication & profiles
├── deploy/                     # Deployment scripts & configs
│   ├── django/                 # Django server deployment
│   ├── adk-agent/              # ADK agent deployment
│   ├── quick_deploy.sh         # Quick deploy script (Linux/Mac)
│   ├── quick_deploy.ps1        # Quick deploy script (Windows)
│   └── start_production.sh     # Production startup script
├── docs/                       # Documentation
│   ├── DEPLOYMENT_GUIDE.md     # Complete deployment guide
│   └── README_DEPLOYMENT.md    # Quick deployment guide
├── tests/                      # Test files
├── static/                     # Static files
├── media/                      # Media files
└── requirements.txt            # Python dependencies
```

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Production Deployment
```bash
# Quick deploy (Linux/Mac)
cd Server/travel_server
chmod +x deploy/quick_deploy.sh
./deploy/quick_deploy.sh

# Quick deploy (Windows PowerShell)
cd Server/travel_server
.\deploy\quick_deploy.ps1
```

## 📚 Documentation

- **[Quick Deployment Guide](docs/README_DEPLOYMENT.md)** - Hướng dẫn deploy nhanh
- **[Complete Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Hướng dẫn deploy chi tiết
- **[API Testing Guide](docs/API_TESTING_GUIDE.md)** - Hướng dẫn test API
- **[Authentication Guide](docs/AUTHENTICATION_API_GUIDE.md)** - Hướng dẫn authentication

## 🔗 API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `GET /api/auth/verify/` - Token verification
- `POST /api/auth/logout/` - User logout

### User Management
- `GET /api/user_manager/profile/` - Get user profile
- `PUT /api/user_manager/profile/` - Update user profile

### Travel Services
- `POST /api/travel/recommendations/` - Get travel recommendations
- `GET /api/travel/tools/status/` - Check tools status

### AI Agent
- `POST /api/agent/chat/` - Chat with AI agent
- `GET /api/agent/status/` - Check agent status
- `GET /api/agent/sub-agents/` - List sub-agents

## 🌐 Production URLs

- **Django Server**: `https://django-server-277713629269.us-central1.run.app`
- **ADK Agent Server**: `https://adk-agent-server-277713629269.us-central1.run.app`
- **ADK Web UI**: `https://adk-agent-server-277713629269.us-central1.run.app/dev-ui?app=travel_concierge`

## 🧪 Testing

### Test Authentication
```bash
curl -X POST https://django-server-277713629269.us-central1.run.app/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username":"nero","password":"1234@pass"}'
```

### Test ADK Web UI
```
https://adk-agent-server-277713629269.us-central1.run.app/dev-ui?app=travel_concierge
```

## 📊 Monitoring

### Check Logs
```bash
# Django logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=django-server" --limit=10

# ADK logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=adk-agent-server" --limit=10
```

### Check Service Status
```bash
gcloud run services list --region=us-central1
```

## 🔧 Development

### Project Structure
- **Models**: `models/` - Database models với business logic
- **Serializers**: `serializers/` - Data validation và serialization
- **Services**: `service/` - Business logic layer
- **Validation**: `validation/` - Custom validation classes
- **Views**: `view/` - API endpoints
- **Tests**: `tests/` - Unit tests

### Code Organization
- Mỗi app có cấu trúc: `models/`, `serializers/`, `service/`, `validation/`, `view/`
- Sử dụng relative imports: `from ..models.user_profile import UserProfile`
- Service layer tách biệt business logic khỏi views
- Validation layer riêng biệt với serializers

## 🎯 Features

### ✅ Implemented
- [x] User Authentication với JWT
- [x] User Profile Management
- [x] AI Agent Integration (ADK)
- [x] Travel Recommendations
- [x] Cloud SQL Database
- [x] Google Cloud Deployment
- [x] Docker Containerization
- [x] API Documentation
- [x] Comprehensive Testing

### 🚧 In Progress
- [ ] Voice Chat Integration
- [ ] Advanced Travel Planning
- [ ] Real-time Notifications
- [ ] Payment Integration

## 🛠️ Tech Stack

- **Backend**: Django 4.2.3
- **Database**: MySQL (Cloud SQL)
- **AI Agent**: Google ADK (Agent Development Kit)
- **Authentication**: JWT
- **Deployment**: Google Cloud Run
- **Container**: Docker
- **API**: Django REST Framework
- **Testing**: Django Test Framework

## 📞 Support

### Troubleshooting
1. Check Cloud Run logs first
2. Verify environment variables
3. Test endpoints individually
4. Check Cloud SQL connectivity
5. Review startup scripts

### Common Issues
- **Database Connection**: Check Cloud SQL Proxy is running
- **ADK Agent**: Verify all files are copied in Dockerfile
- **API Keys**: Ensure environment variables are set correctly

## 📄 License

This project is part of the Travel Concierge application.

---

**Last Updated**: July 24, 2025
**Version**: 1.0
**Author**: Travel Concierge Team