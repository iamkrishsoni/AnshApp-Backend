import redis

# Connect to Redis (Ensure Redis is running)
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

