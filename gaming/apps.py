from django.apps import AppConfig
import redis
import os
class GamingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gaming"
    def ready(self):
        r = redis.StrictRedis(
            host=os.environ.get('REDIS_HOST'), 
            port=os.environ.get('REDIS_PORT'), 
            decode_responses=True,
            username=os.environ.get('REDIS_USERNAME'),
            password=os.environ.get('REDIS_PASSWORD')
        )
        r.flushall()
