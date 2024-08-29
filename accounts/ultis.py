import random
from wallet.ultis import save_to_redis, get_from_redis
from dotenv import load_dotenv
from django.utils import timezone
import string

def generate_referral_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def count_open_pouch(user):
    today = timezone.now().strftime('%Y-%m-%d')
    redis_key = f'open_pouch_{user.id}_{today}' 
    open_count = get_from_redis(redis_key) or 0
    open_count = int(open_count)
    return open_count


def count_share_pouch(user):
    today = timezone.now().strftime('%Y-%m-%d') 
    redis_key = f'share_pouch_{user.id}_{today}'
    share_count = get_from_redis(redis_key) or 0
    share_count = int(share_count)
    return share_count