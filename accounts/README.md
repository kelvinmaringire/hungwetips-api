# Accounts App - Headless API Authentication System

A headless REST API authentication system for Django, supporting user registration, login, password management, and profile management.

## Features

- User registration with email verification
- Login with email or username + password
- JWT-based authentication
- Token refresh and blacklisting
- Password change (authenticated)
- Password reset (forgot password flow)
- User profile management
- Email verification

## API Endpoints

All endpoints are prefixed with `/api/accounts/`

### Authentication

#### 1. User Registration
**POST** `/api/accounts/register/`

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john.doe@example.com",
  "password1": "SecurePassword123!",
  "password2": "SecurePassword123!"
}
```

**Response (201 Created):**
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john.doe@example.com",
    "email_verified": false,
    ...
  },
  "access_token": "...",
  "refresh_token": "...",
  "message": "Registration successful."
}
```

#### 2. User Login
**POST** `/api/accounts/login/`

**Request Body:**
```json
{
  "login": "john.doe@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "user": {...},
  "access_token": "...",
  "refresh_token": "...",
  "message": "Login successful."
}
```

#### 3. User Logout
**POST** `/api/accounts/logout/`

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Email Verification

#### 4. Verify Email
**POST** `/api/accounts/verify-email/`

**Request Body:**
```json
{
  "key": "uidb64-token"
}
```

#### 5. Resend Verification Email
**POST** `/api/accounts/resend-verification/`

**Request Body:**
```json
{
  "email": "john.doe@example.com"
}
```

### Password Management

#### 6. Change Password
**PUT/PATCH** `/api/accounts/change-password/`

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "old_password": "OldPassword123!",
  "new_password1": "NewSecurePassword123!",
  "new_password2": "NewSecurePassword123!"
}
```

#### 7. Request Password Reset
**POST** `/api/accounts/password-reset/`

**Request Body:**
```json
{
  "email": "john.doe@example.com"
}
```

#### 8. Validate Password Reset Token
**GET** `/api/accounts/password-reset/validate/{token_key}/`

#### 9. Confirm Password Reset
**POST** `/api/accounts/password-reset-confirm/`

**Request Body:**
```json
{
  "token_key": "uidb64-token",
  "new_password1": "NewSecurePassword123!",
  "new_password2": "NewSecurePassword123!"
}
```

### User Profile

#### 10. Get/Update User Profile
**GET/PUT** `/api/accounts/profile/`

**Headers:** `Authorization: Bearer <access_token>`

**GET Response:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "email_verified": true,
  "dob": "1990-01-01",
  "sex": "M",
  "physical_address": "123 Main St",
  "phone_number": "+1234567890"
}
```

### Token Refresh

**POST** `/api/token/refresh/`

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## Configuration

### Environment Variables

Add to `.env` file:

```env
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@hungwetips.com

# Frontend URL (for email links)
FRONTEND_URL=http://localhost:9000
```

### Django Settings

- `AUTH_USER_MODEL = 'accounts.CustomUser'` (already configured)
- JWT authentication configured in REST_FRAMEWORK settings
- Token blacklist enabled

## Usage Example

```python
import requests

# Register
response = requests.post('http://localhost:8000/api/accounts/register/', json={
    'username': 'testuser',
    'email': 'test@example.com',
    'password1': 'SecurePass123!',
    'password2': 'SecurePass123!'
})
data = response.json()
access_token = data['access_token']

# Login
response = requests.post('http://localhost:8000/api/accounts/login/', json={
    'login': 'test@example.com',
    'password': 'SecurePass123!'
})
data = response.json()
access_token = data['access_token']

# Get Profile
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get('http://localhost:8000/api/accounts/profile/', headers=headers)
profile = response.json()
```

## CustomUser Model

Extended Django AbstractUser with:
- `email_verified` - Email verification status
- `dob` - Date of birth (optional)
- `sex` - Gender (M/F/O, optional)
- `physical_address` - Physical address (optional)
- `phone_number` - Phone number (optional)
