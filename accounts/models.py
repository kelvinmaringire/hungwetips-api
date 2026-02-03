from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """Custom user model extending AbstractUser with email verification and additional fields."""
    email_verified = models.BooleanField(default=False)
    dob = models.DateField(null=True, blank=True)
    sex_choices = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    sex = models.CharField(max_length=1, choices=sex_choices, null=True, blank=True)
    physical_address = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username
