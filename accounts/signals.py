from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser

# @receiver(post_save, sender=CustomUser)
# def set_claim_expire(sender, instance, created, **kwargs):
#     if created:
#         instance.claim_expire = timezone.now() + timedelta(minutes=30)
#         instance.save()