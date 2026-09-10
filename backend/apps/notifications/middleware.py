from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken

from apps.accounts.models import User


@database_sync_to_async
def get_user_from_token(raw_token):
    try:
        token = UntypedToken(raw_token)
        return User.objects.get(id=token["user_id"], is_active=True)
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token", [None])[0]
        if not token:
            for key, value in scope.get("headers", []):
                if key.lower() == b"authorization" and value.lower().startswith(b"bearer "):
                    token = value[7:].decode()
                    break
        scope["user"] = await get_user_from_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)

