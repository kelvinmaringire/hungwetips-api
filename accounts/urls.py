"""
URL configuration for accounts app.
Defines all authentication-related API endpoints.
"""
from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ChangePasswordView,
    PasswordResetView,
    PasswordResetConfirmView,
    PasswordResetTokenValidateView,
    VerifyEmailView,
    ResendVerificationEmailView,
    UserProfileView,
)

app_name = 'accounts'

urlpatterns = [
    # Registration and Login
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Email Verification
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),
    
    # Password Management
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/validate/<str:token_key>/', PasswordResetTokenValidateView.as_view(), name='password_reset_validate'),
    path('password-reset-confirm/<str:token_key>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm_with_token'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # User Profile
    path('profile/', UserProfileView.as_view(), name='profile'),
]
