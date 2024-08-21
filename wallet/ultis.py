import random
import redis
import os
from dotenv import load_dotenv
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

def delete_from_redis(key):
    r.delete(key)
