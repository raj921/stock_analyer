import time
from django.core.cache import cache

def rate_limit(key, limit, period):
   
    current_time = int(time.time())
    cache_key = f"rate_limit:{key}:{current_time // period}"
    
    count = cache.get(cache_key, 0)
    
    if count >= limit:
        return False
    
    cache.set(cache_key, count + 1, timeout=period)
    return True
