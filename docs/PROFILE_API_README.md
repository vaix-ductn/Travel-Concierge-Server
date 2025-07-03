# Profile Management API

## Tổng quan

API này cung cấp các endpoint để quản lý thông tin profile người dùng trong Travel Concierge App, bao gồm:

- Lấy thông tin profile
- Cập nhật thông tin profile
- Đổi mật khẩu
- Tạo profile mới (cho testing)

## Cấu trúc Database

### Bảng `user_profiles`

```sql
CREATE TABLE user_profiles (
    id CHAR(36) PRIMARY KEY,  -- UUID7 format
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    interests TEXT NOT NULL,
    avatar_url VARCHAR(500) NULL,

    -- Travel preferences từ itinerary_custom.json
    passport_nationality VARCHAR(100) NULL,
    seat_preference VARCHAR(50) NULL,
    food_preference TEXT NULL,
    allergies JSON NULL,
    likes JSON NULL,
    dislikes JSON NULL,
    price_sensitivity JSON NULL,
    home_address TEXT NULL,
    local_prefer_mode VARCHAR(50) NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_email (email),
    INDEX idx_username (username)
);
```

## API Endpoints

### 1. GET /api/profile
**Lấy thông tin profile người dùng**

```bash
curl -X GET "http://localhost:8001/api/profile" \
  -H "Content-Type: application/json"
```

**Response Success (200):**
```json
{
  "success": true,
  "message": "Profile retrieved successfully",
  "data": {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "username": "Alan Love",
    "email": "alanlovelq@gmail.com",
    "address": "Ha Noi, Viet Nam",
    "interests": "Travel, Photography, Food",
    "avatar_url": null,
    "passport_nationality": "Vietnamese",
    "seat_preference": "window",
    "food_preference": "Japanese cuisine - Ramen, Sushi, Sashimi",
    "allergies": [],
    "likes": ["temples", "beaches", "mountains", "museums"],
    "dislikes": ["remote locations", "dangerous areas"],
    "price_sensitivity": ["mid-range"],
    "home_address": "2-chōme-40-2 Harayama, Midori Ward, Saitama, 336-0931",
    "local_prefer_mode": "drive",
    "created_at": "2024-01-01T00:00:00.000Z",
    "updated_at": "2024-01-01T00:00:00.000Z"
  }
}
```

### 2. PUT /api/profile/update
**Cập nhật thông tin profile**

```bash
curl -X PUT "http://localhost:8001/api/profile/update" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Alan Smith",
    "email": "alansmith@gmail.com",
    "address": "Ho Chi Minh City, Viet Nam",
    "interests": "Travel, Photography, Food, Adventure",
    "passport_nationality": "Vietnamese",
    "seat_preference": "aisle",
    "food_preference": "Italian cuisine",
    "likes": ["museums", "beaches", "hiking"],
    "price_sensitivity": ["luxury"]
  }'
```

**Response Success (200):**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "username": "Alan Smith",
    "email": "alansmith@gmail.com",
    // ... updated fields
  }
}
```

**Response Error (400):**
```json
{
  "success": false,
  "message": "Validation failed",
  "data": {
    "errors": {
      "email": "Invalid email format",
      "username": "Username is required"
    }
  }
}
```

### 3. PUT /api/profile/change-password
**Đổi mật khẩu**

```bash
curl -X PUT "http://localhost:8001/api/profile/change-password" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "oldpassword123",
    "new_password": "newpassword456",
    "confirm_password": "newpassword456"
  }'
```

**Response Success (200):**
```json
{
  "success": true,
  "message": "Password changed successfully",
  "data": null
}
```

**Response Error (400):**
```json
{
  "success": false,
  "message": "Current password is incorrect",
  "data": null
}
```

### 4. POST /api/profile/create
**Tạo profile mới (cho testing)**

```bash
curl -X POST "http://localhost:8001/api/profile/create" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "New User",
    "email": "newuser@example.com",
    "password": "password123",
    "confirm_password": "password123",
    "address": "Test Address",
    "interests": "Testing APIs"
  }'
```

## Setup và Deployment

### 1. Database Migration

```bash
# Tạo migration files
python manage.py makemigrations travel_concierge

# Chạy migrations
python manage.py migrate
```

### 2. Load Sample Data

```bash
# Sử dụng seed_data command (recommended)
python manage.py seed_data

# Force recreate nếu users đã tồn tại
python manage.py seed_data --force
```

### 3. Docker Setup

```bash
# Build và start containers
docker-compose up --build

# Database sẽ available tại:
# Host: localhost
# Port: 3309
# Database: travel_concierge
# Username: travel_concierge
# Password: travel_concierge
```

## Validation Rules

### Profile Update
- **username**: 1-100 ký tự, bắt buộc
- **email**: Valid email format, unique, bắt buộc
- **address**: 1-500 ký tự, bắt buộc
- **interests**: 1-1000 ký tự, bắt buộc
- **avatar_url**: Valid URL format (optional)

### Password Change
- **current_password**: Phải khớp với password hiện tại
- **new_password**: 8-128 ký tự, thỏa mãn Django password validators
- **confirm_password**: Phải khớp với new_password

## Rate Limiting

- **GET /profile**: 100 requests/15 minutes
- **PUT /profile/update**: 100 requests/15 minutes
- **PUT /profile/change-password**: 5 requests/15 minutes

## Security Features

- Password hashing với bcrypt
- Input validation và sanitization
- Rate limiting
- JSON field validation
- Email uniqueness check

## Testing

```bash
# Chạy tất cả tests
python manage.py test travel_concierge

# Chạy specific test class
python manage.py test travel_concierge.tests.ProfileAPITestCase

# Chạy với coverage
coverage run --source='.' manage.py test travel_concierge
coverage report
```

## Sample Data Structure

Dữ liệu mẫu dựa trên `itinerary_custom.json`:

```json
{
  "username": "Alan Love",
  "email": "alanlovelq@gmail.com",
  "passport_nationality": "Vietnamese",
  "seat_preference": "window",
  "food_preference": "Japanese cuisine - Ramen, Sushi, Sashimi",
  "allergies": [],
  "likes": [
    "temples", "beaches", "mountains", "museums",
    "nightlife", "hiking", "hot springs", "beautiful scenery"
  ],
  "dislikes": [
    "remote locations", "dangerous areas",
    "places unsuitable for families with small children"
  ],
  "price_sensitivity": ["mid-range"],
  "home_address": "2-chōme-40-2 Harayama, Midori Ward, Saitama, 336-0931",
  "local_prefer_mode": "drive"
}
```

## AI Integration

Profile data có thể được sử dụng để tạo context cho AI Agent:

```json
{
  "user_scenario": {
    "user_name": "Alan Love",
    "user_email": "alanlovelq@gmail.com",
    "user_location": "Ha Noi, Viet Nam",
    "user_interests": "Travel, Photography, Food",
    "user_preferences": {
      "passport_nationality": "Vietnamese",
      "seat_preference": "window",
      "food_preference": "Japanese cuisine",
      "likes": ["temples", "beaches"],
      "price_sensitivity": ["mid-range"]
    }
  }
}
```

## Ghi chú cần update phía App

Các trường dữ liệu mở rộng từ `itinerary_custom.json` cần được bổ sung vào payload của App:

1. **passport_nationality** - Quốc tịch hộ chiếu
2. **seat_preference** - Sở thích chỗ ngồi (window/aisle/middle)
3. **food_preference** - Sở thích đồ ăn
4. **allergies** - Danh sách dị ứng (JSON array)
5. **likes** - Sở thích du lịch (JSON array)
6. **dislikes** - Không thích (JSON array)
7. **price_sensitivity** - Mức độ nhạy cảm giá (JSON array)
8. **home_address** - Địa chỉ nhà
9. **local_prefer_mode** - Phương tiện di chuyển ưa thích (drive/walk/public_transport)

Những trường này sẽ giúp AI Agent đưa ra các gợi ý du lịch phù hợp hơn với sở thích cá nhân của user.