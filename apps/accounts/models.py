"""
User accounts models for Gamefowl Management System.
"""
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Extended user profile with role-based access.
    Links to Django's built-in User model.
    """

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        BREEDER = 'breeder', 'Breeder'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.BREEDER
    )
    farm_name = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    # Profile image (optional)
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == self.Role.ADMIN

    @property
    def is_breeder(self):
        """Check if user has breeder role."""
        return self.role == self.Role.BREEDER

    @property
    def display_name(self):
        """Return farm name if set, otherwise username."""
        return self.farm_name if self.farm_name else self.user.username
