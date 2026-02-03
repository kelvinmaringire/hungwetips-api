"""
API views for authentication endpoints.
Handles registration, login, logout, password management, and user profile.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth.tokens import default_token_generator

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
)
from .services import (
    get_tokens_for_user,
    send_verification_email,
    send_password_reset_email,
)

User = get_user_model()


def build_auth_response(user, message):
    """Build standardized authentication response with user data and tokens."""
    tokens = get_tokens_for_user(user)
    user_serializer = UserSerializer(user)
    return {
        'user': user_serializer.data,
        'access_token': tokens['access'],
        'refresh_token': tokens['refresh'],
        'tokens': tokens,
        'message': message
    }


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    
    POST /api/accounts/register/
    Creates a new user account.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send verification email
        try:
            send_verification_email(request, user)
        except Exception as e:
            # Log error but don't fail registration
            pass
        
        return Response(
            build_auth_response(user, 'Registration successful.'),
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """
    User login endpoint.
    
    POST /api/accounts/login/
    Authenticates user with email/username and password, returns JWT tokens.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response(
            build_auth_response(user, 'Login successful.'),
            status=status.HTTP_200_OK
        )


class LogoutView(APIView):
    """
    User logout endpoint.
    
    POST /api/accounts/logout/
    Blacklists the refresh token to invalidate user session.
    Accepts refresh_token in request body (field names: 'refresh_token' or 'refresh').
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = (
            request.data.get('refresh_token') or
            request.data.get('refresh') or
            request.data.get('refreshToken')
        )
        
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({
                    'message': 'Successfully logged out.'
                }, status=status.HTTP_200_OK)
            except TokenError:
                return Response({
                    'error': 'Invalid refresh token.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': 'Successfully logged out.',
            'warning': 'No refresh token provided. If you have a refresh token, please include it in the request body.'
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    Change password endpoint.
    
    PUT /api/accounts/change-password/
    PATCH /api/accounts/change-password/
    Allows authenticated users to change their password.
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, *args, **kwargs):
        return self._change_password(request)

    def patch(self, request, *args, **kwargs):
        return self._change_password(request)

    def _change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Password changed successfully.'
        }, status=status.HTTP_200_OK)


class PasswordResetView(APIView):
    """
    Request password reset endpoint.
    
    POST /api/accounts/password-reset/
    Sends password reset email to user.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(request, user)
            return Response({
                'message': 'Password reset email has been sent.'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                'message': 'If an account exists with this email, a password reset link has been sent.'
            }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset endpoint.
    
    POST /api/accounts/password-reset-confirm/
    Resets password using token from email.
    
    Accepts token in multiple formats:
    1. URL path: /api/accounts/password-reset-confirm/{uidb64}-{token}/
    2. Request body: {"token_key": "uidb64-token", "new_password1": "...", "new_password2": "..."}
    3. Request body: {"uid": "uidb64", "token": "token", "new_password1": "...", "new_password2": "..."}
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, token_key=None):
        data = request.data.copy()
        if token_key:
            data['token_key'] = token_key
        
        serializer = PasswordResetConfirmSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        uid, token = serializer.get_uid_and_token()
        new_password = serializer.validated_data['new_password1']
        
        try:
            decoded_uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=decoded_uid)
            
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({
                    'message': 'Password has been reset successfully.'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid or expired token.'
                }, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            return Response({
                'error': f'Invalid token or user not found: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetTokenValidateView(APIView):
    """
    Validate password reset token endpoint.
    
    GET /api/accounts/password-reset/validate/{token_key}/
    Validates if a password reset token is valid without resetting the password.
    Useful for frontend to check if the token is valid before showing the reset form.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, token_key):
        if '-' not in token_key:
            return Response({
                'valid': False,
                'error': 'Invalid token format. Expected: uidb64-token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            uid, token = token_key.split('-', 1)
            decoded_uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=decoded_uid)
            
            if default_token_generator.check_token(user, token):
                return Response({
                    'valid': True,
                    'message': 'Token is valid.'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'valid': False,
                    'error': 'Invalid or expired token.'
                }, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            return Response({
                'valid': False,
                'error': f'Invalid token format: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """
    Email verification endpoint.
    
    POST /api/accounts/verify-email/
    Verifies user email using confirmation key from email.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        key = request.data.get('key')
        if not key:
            return Response({
                'error': 'Verification key is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if '-' in key:
                uid, token = key.split('-', 1)
                decoded_uid = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=decoded_uid)
                
                if default_token_generator.check_token(user, token):
                    user.email_verified = True
                    user.save()
                    return Response({
                        'message': 'Email verified successfully.'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': 'Invalid or expired verification key.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'error': 'Invalid verification key format.'
                }, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            return Response({
                'error': f'Invalid verification key: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(APIView):
    """
    Resend verification email endpoint.
    
    POST /api/accounts/resend-verification/
    Resends email verification to user.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'error': 'Email is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if user.email_verified:
                return Response({
                    'message': 'Email is already verified.'
                }, status=status.HTTP_200_OK)
            
            send_verification_email(request, user)
            return Response({
                'message': 'Verification email has been sent.'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                'error': 'No user found with this email address.'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    User profile endpoint.
    
    GET /api/accounts/profile/
    PUT /api/accounts/profile/
    Retrieve or update authenticated user profile.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
