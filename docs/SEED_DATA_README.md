# 🌱 Seed Data Management

## Overview
Seed data command for creating test users and user profiles in the Travel Concierge system.

## Features
- Creates both Django Users (auth_user table) and UserProfile records (user_profiles table)
- Uses hard-coded travel preferences based on `itinerary_custom.json` data
- Creates 4 different types of test users
- Provides force override option
- Shows detailed creation summary

## Usage

### Basic Command
```bash
# Create seed data
python manage.py seed_data

# Or in Docker
docker-compose run web python manage.py seed_data
```

### Force Recreate (if users exist)
```bash
# Recreate existing users
python manage.py seed_data --force

# Or in Docker
docker-compose run web python manage.py seed_data --force
```

## Test Users Created

### 1. 🔧 System Administrator
- **Username:** `admin`
- **Email:** `admin@travelconcierge.com`
- **Password:** `TravelAdmin@2024`
- **Role:** Super admin with Django admin access
- **Travel Style:** Efficiency-focused, technology-oriented

### 2. 👤 Nero Tran (Sample User from itinerary_custom.json)
- **Username:** `nero`
- **Email:** `tranamynero@gmail.com`
- **Password:** `1234@pass`
- **Role:** Regular user
- **Travel Style:** Vietnamese traveler with preferences from itinerary_custom.json
- **Hard-coded data:**
  - Passport: Vietnamese
  - Seat: window
  - Food: Japanese cuisine - Ramen, Sushi, Sashimi
  - Likes: temples, beaches, mountains, museums, nightlife, hiking, hot springs, beautiful scenery
  - Dislikes: remote locations, dangerous areas, places unsuitable for families with small children
  - Price: mid-range
  - Home: 2-chōme-40-2 Harayama, Midori Ward, Saitama, 336-0931
  - Transport: drive

### 3. 🧪 Test User
- **Username:** `test_user`
- **Email:** `testuser@example.com`
- **Password:** `TestUser@2024`
- **Role:** Regular user
- **Travel Style:** American traveler, budget to mid-range, likes hiking/museums

### 4. 🎭 Demo Traveler
- **Username:** `demo_traveler`
- **Email:** `demo@travelconcierge.com`
- **Password:** `DemoTravel@2024`
- **Role:** Regular user
- **Travel Style:** British luxury traveler, prefers fine dining and premium accommodations

## Data Sources

### Hard-coded Nero Tran Profile
Nero Tran's profile uses **hard-coded values** extracted from `travel_concierge/profiles/itinerary_custom.json`:

```python
'user_profile': {
    'passport_nationality': 'Vietnamese',
    'seat_preference': 'window',
    'food_preference': 'Japanese cuisine - Ramen, Sushi, Sashimi',
    'allergies': [],
    'likes': ['temples', 'beaches', 'mountains', 'museums', 'nightlife', 'hiking', 'hot springs', 'beautiful scenery'],
    'dislikes': ['remote locations', 'dangerous areas', 'places unsuitable for families with small children'],
    'price_sensitivity': ['mid-range'],
    'home_address': '2-chōme-40-2 Harayama, Midori Ward, Saitama, 336-0931',
    'local_prefer_mode': 'drive',
}
```

**Note:** The command does NOT read from the JSON file dynamically. All data is hard-coded based on the JSON content for consistent testing.

## Database Tables

### 1. auth_user (Django Users)
- Standard Django authentication users
- Used for login/session management
- Admin users have `is_staff=True` and `is_superuser=True`

### 2. user_profiles (Travel Profiles)
- Extended user information with travel preferences
- Linked to Django users by email (not foreign key)
- Contains travel-specific data for AI agent

## Command Output Example
```
✅ Created user: admin (admin@travelconcierge.com)
   Profile UUID: 12345678-1234-1234-1234-123456789012
   Django User ID: 1
   Passport: Japanese
   Preferences: ['efficiency', 'technology', 'travel']

✅ Created user: nero (tranamynero@gmail.com)
   Profile UUID: 87654321-4321-4321-4321-210987654321
   Django User ID: 2
   Passport: Vietnamese
   Preferences: ['temples', 'beaches', 'mountains', 'museums', 'nightlife', 'hiking', 'hot springs', 'beautiful scenery']

🎉 Successfully created 4 test users!
📝 Total Django users: 4
👤 Total User profiles: 4

🔐 Login credentials for testing:
   Username: admin
   Password: TravelAdmin@2024
   Email: admin@travelconcierge.com
```

## API Testing

After seeding data, you can test the user profile APIs:

```bash
# List all user profiles (to get profile UUIDs)
curl -X GET "http://localhost:8001/api/user_manager/profiles/"

# Get specific user profile by UUID
curl -X GET "http://localhost:8001/api/user_manager/profile/{PROFILE_UUID}/"

# Update user profile by UUID
curl -X PUT "http://localhost:8001/api/user_manager/profile/{PROFILE_UUID}/update/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Nero Tran Updated",
    "interests": "Travel, Photography, Food, Technology"
  }'

# Change password by profile UUID
curl -X PUT "http://localhost:8001/api/user_manager/profile/{PROFILE_UUID}/change-password/" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "1234@pass",
    "new_password": "NewPassword@2024"
  }'

# Create new profile
curl -X POST "http://localhost:8001/api/user_manager/profile/create/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "New User",
    "email": "newuser@example.com",
    "address": "New Address",
    "interests": "New Interests"
  }'
```

**Note:** Replace `{PROFILE_UUID}` with the actual UUID from the profiles list response.

## Django Admin Access

After seeding, login to Django admin with:
- **URL:** `http://localhost:8001/admin/`
- **Username:** `admin`
- **Password:** `TravelAdmin@2024`

## Troubleshooting

### Migration Required
If you get migration errors:
```bash
python manage.py migrate
# Or
docker-compose run web python manage.py migrate
```

### Force Recreate
If users already exist and you want to recreate:
```bash
python manage.py seed_data --force
```

## Development Notes

- User profiles use UUID4 primary keys (not UUID7 due to Python version)
- Passwords are properly hashed using Django's `make_password()`
- Both Django auth and custom profile systems are populated
- Email is used as the linking field between systems
- Nero Tran's travel preferences are **hard-coded from itinerary_custom.json** for consistent testing
- No file I/O dependencies - all data is embedded in the command