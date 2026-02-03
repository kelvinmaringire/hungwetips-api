"""
Service layer for authentication business logic.
Handles token generation, email sending, and other authentication-related operations.
"""
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings


def get_tokens_for_user(user):
    """Generate JWT access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def send_verification_email(request, user):
    """Send email verification to user."""
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:9000')
    verification_url = f"{frontend_url}/verify-email?key={uidb64}-{token}"
    
    subject = 'Verify your email address'
    message = f'Please verify your email by clicking the link: {verification_url}'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hungwetips.com')
    
    send_mail(subject, message, from_email, [user.email], fail_silently=False)


def send_password_reset_email(request, user):
    """Send password reset email to user."""
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:9000')
    reset_url = f"{frontend_url}/password/reset/key/{uidb64}-{token}/"
    
    subject = 'Password reset request'
    message = f'Please reset your password by clicking the link: {reset_url}'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hungwetips.com')
    
    send_mail(subject, message, from_email, [user.email], fail_silently=False)
