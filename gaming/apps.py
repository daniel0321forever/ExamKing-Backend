from django.apps import AppConfig
import redis

class GamingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gaming"
    def ready(self):
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        r.flushall()
