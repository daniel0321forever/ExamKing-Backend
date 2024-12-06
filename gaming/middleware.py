# middleware.py
from channels.middleware import BaseMiddleware
from urllib.parse import parse_qs
from django.db import close_old_connections
from asgiref.sync import sync_to_async

class FieldValidateMiddleware(BaseMiddleware):

    async def __call__(self, scope, receive, send):
        # NOTE: in the method, we assume the toke is sent with url query set
        try:
            close_old_connections()
            scope["is_validated"] = True
            query_string = parse_qs(scope["query_string"].decode())

            return await super().__call__(scope, receive, send)
        except Exception as e:
            print(f"Exception {e} occurs when validating field")
            scope["is_validated"] = False
            scope["error"] = e
            return await super().__call__(scope, receive, send)