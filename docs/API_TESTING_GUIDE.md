# 🔧 API Testing Guide - User Manager

## Overview
Guide for testing User Manager APIs with profile UUID-based endpoints.

## Prerequisites
1. Run migrations: `python manage.py migrate`
2. Create seed data: `python manage.py seed_data`
3. Start server: `python manage.py runserver` or `docker-compose up`

## API Endpoints

### 1. 📋 List All Profiles
**GET** `/api/user_manager/profiles/`

```bash
curl -X GET "http://localhost:8001/api/user_manager/profiles/"
```

**Response:**
```json
{
  "success": true,
  "count": 4,
  "data": [
    {
      "profile_uuid": "12345678-1234-1234-1234-123456789012",
      "username": "System Administrator",
      "email": "admin@travelconcierge.com",
      "address": "Travel Concierge HQ, Tokyo, Japan",
      "interests": "System administration, Travel technology",
      "passport_nationality": "Japanese",
      "seat_preference": "aisle",
      "food_preference": "No preference",
      "likes": ["efficiency", "technology", "travel"],
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "profile_uuid": "87654321-4321-4321-4321-210987654321",
      "username": "Nero Tran",
      "email": "tranamynero@gmail.com",
      "address": "Ha Noi, Viet Nam",
      "interests": "Travel, Photography, Food",
      "passport_nationality": "Vietnamese",
      "seat_preference": "window",
      "food_preference": "Japanese cuisine - Ramen, Sushi, Sashimi",
      "likes": ["temples", "beaches", "mountains", "museums"],
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 2. 👤 Get Specific Profile
**GET** `/api/user_manager/profile/{profile_uuid}/`

```bash
# Example with Nero Tran's UUID
curl -X GET "http://localhost:8001/api/user_manager/profile/87654321-4321-4321-4321-210987654321/"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "profile_uuid": "87654321-4321-4321-4321-210987654321",
    "username": "Nero Tran",
    "email": "tranamynero@gmail.com",
    "address": "Ha Noi, Viet Nam",
    "interests": "Travel, Photography, Food",
    "passport_nationality": "Vietnamese",
    "seat_preference": "window",
    "food_preference": "Japanese cuisine - Ramen, Sushi, Sashimi",
    "allergies": [],
    "likes": ["temples", "beaches", "mountains", "museums", "nightlife", "hiking", "hot springs", "beautiful scenery"],
    "dislikes": ["remote locations", "dangerous areas", "places unsuitable for families with small children"],
    "price_sensitivity": ["mid-range"],
    "home_address": "2-chōme-40-2 Harayama, Midori Ward, Saitama, 336-0931",
    "local_prefer_mode": "drive",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### 3. ✏️ Update Profile
**PUT** `/api/user_manager/profile/{profile_uuid}/update/`

```bash
# Update Nero Tran's profile
curl -X PUT "http://localhost:8001/api/user_manager/profile/87654321-4321-4321-4321-210987654321/update/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Nero Tran Updated",
    "interests": "Travel, Photography, Food, Technology, Gaming",
    "address": "Ho Chi Minh City, Viet Nam",
    "likes": ["temples", "beaches", "mountains", "museums", "nightlife", "hiking", "hot springs", "beautiful scenery", "technology"]
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "profile_uuid": "87654321-4321-4321-4321-210987654321",
    "username": "Nero Tran Updated",
    "email": "tranamynero@gmail.com",
    "address": "Ho Chi Minh City, Viet Nam",
    "interests": "Travel, Photography, Food, Technology, Gaming",
    "likes": ["temples", "beaches", "mountains", "museums", "nightlife", "hiking", "hot springs", "beautiful scenery", "technology"],
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

### 4. 🔐 Change Password
**PUT** `/api/user_manager/profile/{profile_uuid}/change-password/`

```bash
# Change Nero Tran's password
curl -X PUT "http://localhost:8001/api/user_manager/profile/87654321-4321-4321-4321-210987654321/change-password/" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "1234@pass",
    "new_password": "NewSecurePass@2024",
    "confirm_password": "NewSecurePass@2024"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

### 5. ➕ Create New Profile
**POST** `/api/user_manager/profile/create/`

```bash
curl -X POST "http://localhost:8001/api/user_manager/profile/create/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "New Traveler",
    "email": "newtraveler@example.com",
    "password": "SecurePass@2024",
    "address": "Bangkok, Thailand",
    "interests": "Street food, Markets, Temples",
    "passport_nationality": "Thai",
    "seat_preference": "aisle",
    "food_preference": "Spicy Thai cuisine",
    "allergies": ["shellfish"],
    "likes": ["street food", "temples", "markets", "nightlife"],
    "dislikes": ["tourist traps"],
    "price_sensitivity": ["budget-friendly"],
    "home_address": "Bangkok, Thailand",
    "local_prefer_mode": "tuk-tuk"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Profile created successfully",
  "data": {
    "profile_uuid": "11111111-2222-3333-4444-555555555555",
    "username": "New Traveler",
    "email": "newtraveler@example.com",
    "address": "Bangkok, Thailand",
    "interests": "Street food, Markets, Temples",
    "passport_nationality": "Thai",
    "seat_preference": "aisle",
    "food_preference": "Spicy Thai cuisine",
    "allergies": ["shellfish"],
    "likes": ["street food", "temples", "markets", "nightlife"],
    "dislikes": ["tourist traps"],
    "price_sensitivity": ["budget-friendly"],
    "home_address": "Bangkok, Thailand",
    "local_prefer_mode": "tuk-tuk",
    "created_at": "2024-01-01T12:30:00Z",
    "updated_at": "2024-01-01T12:30:00Z"
  }
}
```

## Error Responses

### Profile Not Found
```json
{
  "detail": "Not found."
}
```

### Validation Errors
```json
{
  "success": false,
  "errors": {
    "email": ["Email already exists"],
    "new_password": ["Password must contain at least one uppercase letter"]
  }
}
```

### Server Error
```json
{
  "error": "Unable to update user profile with UUID 87654321-4321-4321-4321-210987654321"
}
```

## Testing Workflow

### 1. Get Profile UUIDs
```bash
# First, get all profile UUIDs
curl -X GET "http://localhost:8001/api/user_manager/profiles/" | jq '.data[].profile_uuid'
```

### 2. Test Individual Profile
```bash
# Use a specific profile UUID for testing
PROFILE_UUID="87654321-4321-4321-4321-210987654321"

# Get profile
curl -X GET "http://localhost:8001/api/user_manager/profile/$PROFILE_UUID/"

# Update profile
curl -X PUT "http://localhost:8001/api/user_manager/profile/$PROFILE_UUID/update/" \
  -H "Content-Type: application/json" \
  -d '{"username": "Updated Name"}'

# Change password
curl -X PUT "http://localhost:8001/api/user_manager/profile/$PROFILE_UUID/change-password/" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "1234@pass",
    "new_password": "NewPass@2024",
    "confirm_password": "NewPass@2024"
  }'
```

## Seed Data Profile UUIDs

After running `python manage.py seed_data`, you'll have these test profiles:

| Username | Email | Default UUID (Example) |
|----------|-------|-------------------------|
| admin | admin@travelconcierge.com | Use profiles API to get real UUID |
| nero | tranamynero@gmail.com | Use profiles API to get real UUID |
| test_user | testuser@example.com | Use profiles API to get real UUID |
| demo_traveler | demo@travelconcierge.com | Use profiles API to get real UUID |

**Note:** Profile UUIDs are generated randomly, so use the profiles list API to get actual UUIDs.

## Tips

1. **Always get fresh profile UUIDs** from `/profiles/` endpoint
2. **UUIDs are case-sensitive** - copy exactly
3. **Use jq for JSON parsing**: `curl ... | jq '.data[0].profile_uuid'`
4. **Check logs** in `logs/profile.log` for debugging
5. **Passwords require**: 8+ chars, uppercase, lowercase, digit