from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from .models import Wallet, UserStake

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance, sniff_coin=0)


@receiver(post_save, sender=UserStake)
def create_user_stake(sender, instance:UserStake, created, **kwargs):
    user_wallet = Wallet.objects.get(user=instance.user)
    user_wallet.sniff_coin -= instance.sniff_coin_stake_amount
    user_wallet.save()

