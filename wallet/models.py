import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
# Create your models here.
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_wallet_id = models.CharField(max_length=255, unique=True)
    sniff_coin = models.DecimalField(max_digits=10, decimal_places=2, default=100.0)
    sniff = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    cards = models.IntegerField(default=0)
    def __str__(self):
        return f'{self.user.username} Wallet'
    
class GiveawayPouch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='giveaway_pouch')
    sniff_coin = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    expired_date = models.DateTimeField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.expired_date:
            self.expired_date = timezone.now() + timedelta(minutes=30)
        super(GiveawayPouch, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} Pouch'

class UserStake(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    end_datetime = models.DateTimeField(blank=True, null=True)
    sniff_coin_stake_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    

class DailyStake(models.Model):
    daily_sniff = models.DecimalField(max_digits=10, decimal_places=2, default=1000.0)
    date = models.DateField(blank=True, null=True)
    def __str__(self):
        return f'{self.date} Daily Stake'


class Task(models.Model):
    task_name = models.CharField(max_length=255)
    task_created = models.DateTimeField(auto_now_add=True)
    task_expired = models.DateTimeField(blank=True, null=True)
    total_card_reward = models.IntegerField(default=0)
    
    def __str__(self):
        return self.task_name 