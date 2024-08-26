import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, Group, Permission
# Create your models here.

User = get_user_model()
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telegram_id = models.CharField(max_length=255)
    user_level = models.IntegerField(default=1)
    daily_limit_open_pouch = models.IntegerField(default=1)
    daily_limit_share_pouch = models.IntegerField(default=1)
    def __str__(self):
        return f'{self.user.username} Profile'


class User(AbstractUser):
    telegram_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',  # Change this to a unique related_name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_set_permissions',  # Change this to a unique related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )