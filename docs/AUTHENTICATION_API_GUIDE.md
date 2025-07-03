# Authentication API Guide

## Overview

This guide provides comprehensive documentation for the Travel Concierge Authentication API. The authentication system implements JWT-based authentication with advanced security features including rate limiting, account lockout, and token blacklisting.

## Base URL

```
http://localhost:8001/api
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Create Test Users

```bash
python manage.py create_test_users
```

### 4. Start Development Server

```bash
python manage.py runserver 8001
```

## API Endpoints

### 1. Login User

**Endpoint:** `POST /api/auth/login/`

**Description:** Authenticates user credentials and returns JWT token with user data.

**Request:**
```json
{
    "username": "alan_love",
    "password": "SecurePassword123!"
}
```

**Success Response (200):**
```json
{
    "success": true,
    "message": "Login successful",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": "user_12345",
        "username": "alan_love",
        "email": "alanlovelq@gmail.com",
        "full_name": "Alan Love",
        "avatar_url": "https://example.com/avatars/alan_love.jpg",
        "address": "Ha Noi, Viet Nam",
        "interests": ["Travel", "Photography", "Food"]
    }
}
```

**Error Responses:**
- **400 Bad Request:** Invalid input data
- **401 Unauthorized:** Invalid credentials
- **429 Too Many Requests:** Rate limit exceeded

### 2. Verify Token

**Endpoint:** `GET /api/auth/verify/`

**Description:** Verifies JWT token validity and returns user information.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Success Response (200):**
```json
{
    "success": true,
    "message": "Token is valid",
    "user": {
        "id": "user_12345",
        "username": "alan_love",
        "email": "alanlovelq@gmail.com",
        "full_name": "Alan Love",
        "avatar_url": "https://example.com/avatars/alan_love.jpg",
        "address": "Ha Noi, Viet Nam",
        "interests": ["Travel", "Photography", "Food"]
    }
}
```

**Error Responses:**
- **401 Unauthorized:** Invalid or expired token
- **429 Too Many Requests:** Rate limit exceeded

### 3. Logout User

**Endpoint:** `POST /api/auth/logout/`

**Description:** Invalidates JWT token and logs out user.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Success Response (200):**
```json
{
    "success": true,
    "message": "Logout successful"
}
```

**Error Response:**
- **401 Unauthorized:** Invalid or expired token

## Testing Examples

### Using cURL

#### 1. Login
```bash
curl -X POST http://localhost:8001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alan_love",
    "password": "SecurePassword123!"
  }'
```

#### 2. Verify Token
```bash
curl -X GET http://localhost:8001/api/auth/verify/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

#### 3. Logout
```bash
curl -X POST http://localhost:8001/api/auth/logout/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Using Python Requests

```python
import requests
import json

BASE_URL = "http://localhost:8001/api"

# 1. Login
login_data = {
    "username": "alan_love",
    "password": "SecurePassword123!"
}

response = requests.post(f"{BASE_URL}/auth/login/",
                        json=login_data)
login_result = response.json()

if login_result.get('success'):
    token = login_result['token']
    print(f"Login successful! Token: {token[:50]}...")

    # 2. Verify token
    headers = {"Authorization": f"Bearer {token}"}
    verify_response = requests.get(f"{BASE_URL}/auth/verify/",
                                  headers=headers)
    print("Token verification:", verify_response.json())

    # 3. Logout
    logout_response = requests.post(f"{BASE_URL}/auth/logout/",
                                   headers=headers)
    print("Logout result:", logout_response.json())
else:
    print("Login failed:", login_result)
```

## Test User Credentials

The system comes with pre-created test users:

### User 1: Alan Love
- **Username:** `alan_love`
- **Password:** `SecurePassword123!`
- **Email:** `alanlovelq@gmail.com`
- **Full Name:** Alan Love
- **Address:** Ha Noi, Viet Nam
- **Interests:** Travel, Photography, Food

### User 2: Test User
- **Username:** `test_user`
- **Password:** `TestPassword123!`
- **Email:** `test@example.com`
- **Full Name:** Test User
- **Address:** Ho Chi Minh City, Viet Nam
- **Interests:** Technology, Gaming, Music

### User 3: Demo User
- **Username:** `demo_user`
- **Password:** `DemoPassword123!`
- **Email:** `demo@example.com`
- **Full Name:** Demo User
- **Address:** Da Nang, Viet Nam
- **Interests:** Art, Culture, History

## Security Features

### 1. Password Security
- **Minimum Length:** 6 characters
- **Hashing:** bcrypt with salt rounds ≥ 12
- **Storage:** Never stores plain text passwords

### 2. JWT Token Security
- **Algorithm:** HS256 (HMAC with SHA-256)
- **Expiration:** 24 hours
- **Blacklisting:** Tokens are tracked and can be invalidated
- **Secret:** Configurable via environment variables

### 3. Rate Limiting
- **Login Attempts:** Maximum 5 attempts per IP per 15 minutes
- **Token Verification:** Maximum 100 requests per minute per IP
- **Account Lockout:** 30 minutes after 5 failed attempts

### 4. Input Validation
- **Username:** 3-50 characters, alphanumeric and underscore only
- **Password:** 6+ characters minimum
- **Email:** Valid email format required
- **Sanitization:** All inputs are sanitized to prevent injection

## Environment Variables

Create a `.env` file in your project root:

```env
# Django Settings
DJANGO_SECRET_KEY=your-super-secret-django-key-here
DEBUG=True

# Database
DB_ENGINE=django.db.backends.mysql
DB_NAME=travel_concierge
DB_USER=travel_concierge
DB_PASSWORD=travel_concierge
DB_HOST=localhost
DB_PORT=3306

# JWT Authentication
JWT_SECRET=your-super-secret-jwt-key-here
JWT_EXPIRATION=24h
BCRYPT_ROUNDS=12

# Rate Limiting
LOGIN_RATE_LIMIT_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW=900
ACCOUNT_LOCKOUT_DURATION=1800

# Redis Cache
REDIS_URL=redis://127.0.0.1:6379/1
```

## Error Handling

### HTTP Status Codes
- **200:** Success
- **400:** Bad Request (validation errors)
- **401:** Unauthorized (invalid credentials or token)
- **429:** Too Many Requests (rate limiting)
- **500:** Internal Server Error

### Error Response Format
```json
{
    "success": false,
    "message": "Human-readable error message",
    "error_code": "SPECIFIC_ERROR_CODE",
    "details": {
        "field": "Additional error details if applicable"
    }
}
```

### Common Error Codes
- `INVALID_CREDENTIALS`: Wrong username or password
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `ACCOUNT_LOCKED`: Account temporarily locked
- `INVALID_TOKEN`: Invalid or expired JWT token

## API Documentation

Interactive API documentation is available at:
- **Swagger UI:** http://localhost:8001/swagger/
- **ReDoc:** http://localhost:8001/redoc/
- **JSON Schema:** http://localhost:8001/swagger.json

## Testing

### Run Unit Tests
```bash
python manage.py test authentication
```

### Test Coverage
The test suite covers:
- User authentication flow
- Token generation and verification
- Rate limiting functionality
- Account lockout mechanisms
- Password hashing and validation
- Input validation and sanitization

## Integration with Mobile App

### Login Flow
1. User enters credentials in mobile app
2. App sends POST request to `/api/auth/login/`
3. On success, store token and user data locally
4. Use token for authenticated requests

### Session Management
1. Include `Authorization: Bearer <token>` header in all authenticated requests
2. Check token validity on app startup with `/api/auth/verify/`
3. Handle token expiration gracefully
4. Implement auto-logout on token expiration

### Logout Flow
1. Send POST request to `/api/auth/logout/`
2. Clear local storage
3. Navigate to login screen

## Troubleshooting

### Common Issues

1. **"Python was not found" error**
   - Install Python or use `python3` command
   - Check Python is in your PATH

2. **Redis connection error**
   - Install and start Redis server
   - Update REDIS_URL in settings

3. **Database connection error**
   - Check database credentials
   - Ensure database server is running
   - Run migrations: `python manage.py migrate`

4. **Token verification fails**
   - Check JWT_SECRET configuration
   - Ensure token is not expired
   - Verify Authorization header format

### Debug Mode

Enable debug logging by setting `DEBUG=True` in settings. Check logs in:
- Console output
- `logs/profile.log` file

## Support

For technical issues or questions:
1. Check the API documentation at `/swagger/`
2. Review error messages and status codes
3. Check server logs for detailed error information
4. Refer to the test cases for usage examples

## Version History

- **v1.0** - Initial implementation with JWT authentication, rate limiting, and security features

---

**Last Updated:** December 2024
**Author:** Travel Concierge Development Team