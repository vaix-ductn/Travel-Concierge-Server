# Authentication API Specification

## Overview
This document outlines the authentication API endpoints for the Travel Concierge application. The authentication system handles user login, session management, and logout functionality.

## Base URL
```
http://localhost:8001/api
```

## Authentication Endpoints

### 1. Login User
**Endpoint:** `POST /auth/login`

**Description:** Authenticates user credentials and returns authentication token and user data.

**Request:**
```http
POST /auth/login
Content-Type: application/json

{
    "username": "alan_love",
    "password": "SecurePassword123!"
}
```

**Request Body Schema:**
```typescript
interface LoginRequest {
    username: string;    // Required, min 3 chars, max 50 chars
    password: string;    // Required, min 6 chars
}
```

**Response (Success - 200):**
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

**Response (Error - 401):**
```json
{
    "success": false,
    "message": "Invalid username or password"
}
```

**Response (Error - 400):**
```json
{
    "success": false,
    "message": "Username and password are required"
}
```

**Response (Error - 429):**
```json
{
    "success": false,
    "message": "Too many login attempts. Please try again later."
}
```

### 2. Verify Token
**Endpoint:** `GET /auth/verify`

**Description:** Verifies if the provided authentication token is valid and returns user information.

**Request:**
```http
GET /auth/verify
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

**Response (Success - 200):**
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

**Response (Error - 401):**
```json
{
    "success": false,
    "message": "Invalid or expired token"
}
```

### 3. Logout User
**Endpoint:** `POST /auth/logout`

**Description:** Invalidates the user's authentication token and logs them out.

**Request:**
```http
POST /auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

**Response (Success - 200):**
```json
{
    "success": true,
    "message": "Logout successful"
}
```

**Response (Error - 401):**
```json
{
    "success": false,
    "message": "Invalid or expired token"
}
```

## Data Models

### User Data Model
```typescript
interface UserData {
    id: string;              // Unique user identifier
    username: string;        // User's login username
    email: string;           // User's email address
    full_name?: string;      // User's full display name
    avatar_url?: string;     // URL to user's avatar image
    address?: string;        // User's address
    interests?: string[];    // Array of user's interests
}
```

### Authentication Response Model
```typescript
interface LoginResponse {
    success: boolean;        // Indicates if operation was successful
    message?: string;        // Success or error message
    token?: string;          // JWT authentication token (on success)
    user?: UserData;         // User data (on success)
}
```

## Security Requirements

### Password Security
- **Minimum Length:** 6 characters
- **Hashing:** Use bcrypt with salt rounds ≥ 12
- **Storage:** Never store plain text passwords

### Token Security
- **Algorithm:** HS256 (HMAC with SHA-256)
- **Expiration:** 24 hours for access tokens
- **Secret:** Use strong, randomly generated secret key
- **Storage:** Store securely in environment variables

### Rate Limiting
- **Login Attempts:** Maximum 5 attempts per IP per 15 minutes
- **Token Verification:** Maximum 100 requests per minute per IP
- **Account Lockout:** Lock account for 30 minutes after 5 failed attempts

### Input Validation
- **Username:** 3-50 characters, alphanumeric and underscore only
- **Password:** 6+ characters, no specific character requirements
- **Sanitization:** Escape all user inputs to prevent injection attacks

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

## Implementation Notes

### Database Schema
```sql
CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    address TEXT,
    interests JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP NULL
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

### Environment Variables
```env
# Authentication
JWT_SECRET=your-super-secret-jwt-key-here
JWT_EXPIRATION=24h
BCRYPT_ROUNDS=12

# Rate Limiting
LOGIN_RATE_LIMIT_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW=900000  # 15 minutes in milliseconds
ACCOUNT_LOCKOUT_DURATION=1800000  # 30 minutes in milliseconds
```

### Integration with Travel Concierge App

1. **Login Flow:**
   - User enters username/password in Sign In screen
   - App sends POST request to `/auth/login`
   - On success, store token and user data locally
   - Navigate to Travel Exploration screen
   - Sync user data with ProfileService and GlobalChatService

2. **Session Management:**
   - Check token validity on app startup
   - Include Bearer token in all authenticated API requests
   - Auto-logout on token expiration
   - Refresh token before expiration (future enhancement)

3. **Logout Flow:**
   - User clicks logout button in Profile Settings
   - App sends POST request to `/auth/logout`
   - Clear local storage and navigate to Sign In screen

## Testing Guidelines

### Unit Tests
- Test password hashing and verification
- Test JWT token generation and validation
- Test rate limiting logic
- Test input validation functions

### Integration Tests
- Test complete login flow
- Test token verification with various scenarios
- Test logout functionality
- Test error handling for invalid requests

### Security Tests
- Test SQL injection protection
- Test brute force attack protection
- Test token tampering detection
- Test CORS configuration

## Future Enhancements

1. **Refresh Tokens:** Implement refresh token mechanism for better security
2. **Social Login:** Add Google and Facebook OAuth integration
3. **Multi-Factor Authentication:** Add 2FA support
4. **Password Reset:** Implement forgot password functionality
5. **Email Verification:** Verify email addresses during registration
6. **Account Registration:** Add user registration endpoint

## Support

For technical questions about this API specification, please contact the development team or refer to the project documentation.

**Last Updated:** December 2024
**Version:** 1.0
**Author:** Travel Concierge Development Team