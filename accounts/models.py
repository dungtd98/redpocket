import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(unique=True, max_length=255)
    telegram_id = models.CharField(max_length=255, blank=True, null=True)
    daily_limit_open_pouch = models.IntegerField(default=1)
    daily_limit_share_pouch = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    objects = CustomUserManager()
    claim_expire = models.DateTimeField(blank=True, null=True)
    referral_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    invited_refcode = models.CharField(max_length=10, blank=True, null=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    def save(self, *args, **kwargs):
        if not self.referral_code:
            print("Generating referral code")
            self.referral_code = self.generate_refcode()
        super().save(*args, **kwargs)

    def generate_refcode(self):
        return str(uuid.uuid4())[:8]
    def __str__(self):
        return self.username
