"""
API View Tests for Accounts app (HungweTips).

Tests for authentication and profile API endpoints:
- User registration via POST /api/accounts/register/
- User login via POST /api/accounts/login/
- User profile GET/PATCH via /api/accounts/profile/
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

User = get_user_model()


class RegisterViewTestCase(APITestCase):
    """Test user registration via POST /api/accounts/register/"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/accounts/register/'
        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
        }

    def test_register_success(self):
        """Test successful user registration returns 201, user, tokens and message."""
        response = self.client.post(self.url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('message', response.data)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertTrue(user.check_password('testpass123!'))

class LoginViewTestCase(APITestCase):
    """Test user login via POST /api/accounts/login/"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/accounts/login/'
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123!',
        )

    def test_login_with_username_success(self):
        """Test login with username and password returns tokens."""
        response = self.client.post(
            self.url,
            {'username': 'testuser', 'password': 'testpass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_login_with_email_success(self):
        """Test login with email and password returns tokens."""
        response = self.client.post(
            self.url,
            {'email': 'testuser@example.com', 'password': 'testpass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)

    def test_login_with_login_field_success(self):
        """Test login with 'login' field (username or email) returns tokens."""
        response = self.client.post(
            self.url,
            {'login': 'testuser', 'password': 'testpass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_login_invalid_credentials(self):
        """Test login with wrong password returns 400."""
        response = self.client.post(
            self.url,
            {'username': 'testuser', 'password': 'wrongpass'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileViewTestCase(APITestCase):
    """Test user profile GET/PATCH via /api/accounts/profile/"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/accounts/profile/'
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123!',
            first_name='Test',
            last_name='User',
        )

    def test_get_profile_unauthorized(self):
        """Test GET profile without auth returns 401."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_success(self):
        """Test GET profile when authenticated returns user data."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'testuser@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')

    def test_patch_profile_partial_update(self):
        """Test PATCH profile updates allowed fields."""
        self.client.force_authenticate(user=self.user)
        update_data = {
            'first_name': 'Updated',
            'phone_number': '+1234567890',
            'physical_address': '123 Main St',
        }
        response = self.client.patch(self.url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.phone_number, '+1234567890')
        self.assertEqual(self.user.physical_address, '123 Main St')
