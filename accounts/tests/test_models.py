"""
Model tests for Accounts app (HungweTips).

Tests for CustomUser model: default fields, __str__, and profile fields.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class CustomUserModelTest(TestCase):
    """Tests for CustomUser model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123',
        )

    def test_str_returns_username(self):
        """__str__ returns the username."""
        self.assertEqual(str(self.user), 'testuser')

    def test_email_verified_default_false(self):
        """New user has email_verified=False by default."""
        self.assertFalse(self.user.email_verified)

    def test_optional_fields_default_none(self):
        """Optional profile fields are None by default."""
        self.assertIsNone(self.user.dob)
        self.assertIsNone(self.user.sex)
        self.assertIsNone(self.user.physical_address)
        self.assertIsNone(self.user.phone_number)

    def test_edit_profile_fields(self):
        """CustomUser profile fields can be set and saved."""
        self.user.dob = timezone.now().date()
        self.user.sex = 'M'
        self.user.physical_address = '123 Main St'
        self.user.phone_number = '+1234567890'
        self.user.email_verified = True
        self.user.save()

        self.user.refresh_from_db()
        self.assertEqual(self.user.sex, 'M')
        self.assertEqual(self.user.physical_address, '123 Main St')
        self.assertEqual(self.user.phone_number, '+1234567890')
        self.assertTrue(self.user.email_verified)

    def test_sex_choices(self):
        """Sex field accepts valid choices."""
        for value, _ in User.sex_choices:
            self.user.sex = value
            self.user.save()
            self.user.refresh_from_db()
            self.assertEqual(self.user.sex, value)
