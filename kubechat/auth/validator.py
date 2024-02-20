import base64
import hashlib
import logging
from typing import Any, Optional

from channels.middleware import BaseMiddleware
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from ninja.security import HttpBearer
from ninja.security.http import HttpAuthBase

import config.settings as settings
from kubechat.auth import tv
from kubechat.utils.constant import KEY_USER_ID, KEY_WEBSOCKET_PROTOCOL

logger = logging.getLogger(__name__)

DEFAULT_USER = "kubechat"


def get_user_from_token(token):
    match settings.AUTH_TYPE:
        case "auth0" | "authing":
            payload = tv.verify(token)
            user = payload["sub"]
        case "none":
            user = base64.b64decode(token).decode("ascii")
        case _:
            user = DEFAULT_USER
    return user


class AdminAuth(HttpBearer):
    def authenticate(self, request, token):
        if not settings.ADMIN_TOKEN or token != settings.ADMIN_TOKEN:
            return None

        request.META[KEY_USER_ID] = settings.ADMIN_USER
        return token


class GlobalHTTPAuth(HttpBearer):
    def authenticate(self, request, token):
        request.META[KEY_USER_ID] = get_user_from_token(token)
        return token


class FeishuEventVerification(HttpAuthBase):

    def __init__(self, encrypt_key=None):
        super().__init__()
        self.openapi_scheme = "feishu"
        self.header = "X-Lark-Signature"
        self.encrypt_key = encrypt_key

    def __call__(self, request: HttpRequest) -> Optional[Any]:
        if not self.encrypt_key:
            return True

        timestamp = request.headers.get("X-Lark-Request-Timestamp", None)
        if not timestamp:
            logger.error("Invalid timestamp in header: %s", request.headers)
            return False

        nonce = request.headers.get("X-Lark-Request-Nonce", None)
        if not nonce:
            logger.error("Invalid nonce in header: %s", request.headers)
            return False

        signature = request.headers.get("X-Lark-Signature", None)
        if not signature:
            logger.error("Invalid signature in header: %s", request.headers)
            return False

        bytes_b1 = (timestamp + nonce + self.encrypt_key).encode('utf-8')
        bytes_b = bytes_b1 + request.body
        h = hashlib.sha256(bytes_b)
        if h.hexdigest() != signature:
            logger.error("Invalid signature: %s", request)
            return False

        return True


class WebSocketAuthMiddleware(BaseMiddleware):
    def __init__(self, app):
        self.app = app

    def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])
        path = scope['path']

        if "/web-chats" in path:
            return self.app(scope, receive, send)

        token = headers.get(KEY_WEBSOCKET_PROTOCOL.lower().encode("ascii"), None)
        if token is not None:
            token = token.decode("ascii")
        scope[KEY_WEBSOCKET_PROTOCOL] = token
        scope[KEY_USER_ID] = get_user_from_token(token)
        return self.app(scope, receive, send)


class HTTPAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        path = scope['path']
        if path == "/api/v1/config" or path.startswith("/api/v1/feishu"):
            return await self.inner(scope, receive, send)

        headers = dict(scope["headers"])
        token = headers.get(b"authorization", None)
        if token is None:
            raise PermissionDenied

        token = token.decode("ascii").lstrip("Bearer ")
        user = get_user_from_token(token)
        scope[KEY_USER_ID] = user
        return await self.inner(scope, receive, send)


