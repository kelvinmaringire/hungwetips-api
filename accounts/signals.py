"""
Signal handlers for accounts app.
Handles email verification status updates and other user-related events.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def update_user_email_verified(sender, instance, created, **kwargs):
    """
    Update user's email_verified status when email is confirmed.
    This is a placeholder - email verification is handled via API endpoint.
    """
    pass
