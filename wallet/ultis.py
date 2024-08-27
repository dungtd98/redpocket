import random
import redis
import os
from dotenv import load_dotenv
from django.utils import timezone

load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST')
r = redis.Redis(host=REDIS_HOST, port=6379, db=0)


def divide_into_percentage_array(number):
    # Convert the input number to a float to ensure it's numeric
    number = float(number)

    # The percentage range for each item
    min_percentage = 0.005  # 0.5%
    max_percentage = 0.015  # 1.5%

    # Initialize the result array
    result = []

    # We need 100 items
    for _ in range(100):
        # Randomly generate a value between 0.5% and 1.5% of the input number
        item = random.uniform(min_percentage * number, max_percentage * number)
        result.append(item)

    # Normalize the array so that the sum equals the original number
    total_sum = sum(result)
    normalized_result = [round(x * number / total_sum, 1) for x in result]

    return normalized_result

def get_random_value_from_array(array: list):
    if not array:
        raise ValueError("Array is empty")
    
    index = random.randint(0, len(array) - 1)  # Get a random index
    return array.pop(index), array

def save_to_redis(key, value, expire=None):
    r.set(key, value, ex=expire)


def get_from_redis(key):
    value = r.get(key)
    if value:
        return value.decode('utf-8')  # Chuyển đổi từ byte sang string
    return None

def get_values_with_key_pattern(pattern):
    keys = r.keys(pattern)
    values = [get_from_redis(key) for key in keys]
    return values

def delete_from_redis(key):
    r.delete(key)

def can_open_pouch(user):
    today = timezone.now().strftime('%Y-%m-%d')
    redis_key = f'open_pouch_{user.id}_{today}' 
    open_count = int(get_from_redis(redis_key)) or 0
    print(open_count)
    if open_count < user.daily_limit_open_pouch:
        open_count += 1
        save_to_redis(redis_key, open_count, 86400) 
        return True
    return False  


def can_share_pouch(user):
    today = timezone.now().strftime('%Y-%m-%d') 
    redis_key = f'share_pouch_{user.id}_{today}'
    share_count = get_from_redis(redis_key) or 0
    if share_count < user.userprofile.daily_limit_share_pouch:
        share_count += 1
        save_to_redis(redis_key, share_count, 86400)
        return True 
    return False 
 