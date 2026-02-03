"""
Serializers for the accounts app.
Handles user registration, authentication, and profile management.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user model."""
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                  'email_verified', 'dob', 'sex', 'physical_address', 'phone_number')
        read_only_fields = ('id', 'email_verified')


class RegisterSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    Validates and creates new user accounts.
    """
    username = serializers.CharField(
        max_length=150,
        required=True,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Password must meet Django's password validation requirements."
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Enter the same password as before, for verification."
    )

    def validate_username(self, username):
        """Validate username uniqueness."""
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return username

    def validate_email(self, email):
        """Validate email uniqueness and format."""
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user is already registered with this email address.")
        return email

    def validate_password1(self, password):
        """Validate password using Django validators."""
        validate_password(password)
        return password

    def validate(self, data):
        """Validate that passwords match."""
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password2": "The two password fields didn't match."})
        return data

    def save(self):
        """Create and save the user."""
        user = User.objects.create_user(
            username=self.validated_data['username'],
            email=self.validated_data['email'],
            password=self.validated_data['password1'],
            email_verified=False
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Supports login with either email or username.
    Accepts 'login', 'username', or 'email' field.
    """
    login = serializers.CharField(required=False, help_text="Email or username")
    username = serializers.CharField(required=False, help_text="Username")
    email = serializers.CharField(required=False, help_text="Email")
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, data):
        """Validate login credentials."""
        login = data.get('login') or data.get('username') or data.get('email')
        password = data.get('password')

        if not login:
            raise serializers.ValidationError("Must include 'login', 'username', or 'email' field along with 'password'.")

        if not password:
            raise serializers.ValidationError("Password is required.")

        user = authenticate(username=login, password=password)
        
        if user is None:
            try:
                user_obj = User.objects.get(email=login)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if user is None:
            raise serializers.ValidationError("Unable to log in with provided credentials.")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        
        data['user'] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password.
    Requires old password verification.
    """
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password1 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate_new_password1(self, value):
        """Validate new password using Django validators."""
        validate_password(value, self.context['request'].user)
        return value

    def validate(self, data):
        """Validate that new passwords match."""
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": "The two password fields didn't match."})
        return data

    def save(self):
        """Update user password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password1'])
        user.save()
        return user


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for requesting password reset."""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset with token.
    Accepts either separate uid/token or combined token_key from URL.
    """
    token = serializers.CharField(required=False)
    uid = serializers.CharField(required=False)
    token_key = serializers.CharField(required=False, help_text="Combined format: uidb64-token")
    new_password1 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, data):
        """Validate that either token_key or both uid and token are provided."""
        token_key = data.get('token_key')
        token = data.get('token')
        uid = data.get('uid')
        
        if not token_key and not (token and uid):
            raise serializers.ValidationError(
                "Either 'token_key' (format: uidb64-token) or both 'uid' and 'token' must be provided."
            )
        
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": "The two password fields didn't match."})
        
        return data

    def validate_new_password1(self, value):
        """Validate new password."""
        temp_user = User()
        validate_password(value, temp_user)
        return value

    def get_uid_and_token(self):
        """Extract uid and token from either format.
        
        Token format: uidb64-token
        Since tokens can contain dashes, we split on the FIRST dash only.
        Example: 'MQ-d1b6kd-fc8e2f628c4e8c960ba419a28bc2fbaf' -> uid='MQ', token='d1b6kd-fc8e2f628c4e8c960ba419a28bc2fbaf'
        """
        if self.validated_data.get('token_key'):
            token_key = self.validated_data['token_key']
            if '-' in token_key:
                uid, token = token_key.split('-', 1)
                return uid, token
            raise serializers.ValidationError({"token_key": "Invalid token format. Expected: uidb64-token"})
        return self.validated_data['uid'], self.validated_data['token']
