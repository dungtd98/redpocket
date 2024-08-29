from celery import shared_task
from .models import Wallet, DailyStake, UserStake
from .ultis import save_to_redis, get_from_redis
from django.utils import timezone
from django.db.models import Sum, F, FloatField

@shared_task
def add_tokens_to_user(user_id,pouch_id):
    """
        This task will trigger automatically every 30 minutes
    """
    user_wallet = Wallet.objects.get(user__id=user_id)
    pouch_values_array = get_from_redis(f'giveaway_pouch_{pouch_id}')
    init_value = pouch_values_array.get('init_value')
    total_opened_pouch = 100-len(pouch_values_array.get('values_array'))
    user_wallet.sniff_coin += round(init_value*total_opened_pouch/100,2)
    user_wallet.save()


@shared_task
def create_daily_stake():
    today = timezone.now().date()

    if not DailyStake.objects.filter(date=today).exists():
        daily_stake = DailyStake(date=today)
        daily_stake.save()


@shared_task
def shared_daily_stake():
    today = timezone.now().date()
    daily_stake = DailyStake.objects.get(date=today)
    now = timezone.now()
    end_of_today = now.replace(hour=23, minute=59)
    active_stakes = UserStake.objects.filter(end_datetime__gt=end_of_today)
    total_active_stake_coin = active_stakes.aggregate(total=Sum('sniff_coin_stake_amount'))['total'] or 0

    if total_active_stake_coin > 0:
        active_stakes_with_ratio = active_stakes.annotate(
            stake_ratio=F('sniff_coin_stake_amount') / total_active_stake_coin
        )

        for stake in active_stakes_with_ratio:
            user_stake_ratio = stake.stake_ratio 
            user_stake= UserStake.objects.get(user=stake.user)
            user_stake.earning += daily_stake.daily_sniff * user_stake_ratio
            user_stake.save()