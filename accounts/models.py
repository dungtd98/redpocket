import uuid
from django.db import models
from django.contrib.auth import get_user_model
# Create your models here.

User = get_user_model()
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telegram_id = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.user.username} Profile'


