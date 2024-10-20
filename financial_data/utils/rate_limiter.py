import time
from django.core.cache import cache

def rate_limit(key, limit, period):
    """
    Rate limiter using Django's cache framework.
    
    :param key: Unique identifier for the rate limit (e.g., API endpoint name)
    :param limit: Number of allowed requests per period
    :param period: Time period in seconds
    :return: True if request is allowed, False if rate limit is exceeded
    """
    current_time = int(time.time())
    cache_key = f"rate_limit:{key}:{current_time // period}"
    
    count = cache.get(cache_key, 0)
    
    if count >= limit:
        return False
    
    cache.set(cache_key, count + 1, timeout=period)
    return True
