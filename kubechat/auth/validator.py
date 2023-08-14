import hashlib
import logging
from typing import Optional, Any

from auth0.authentication.token_verifier import (
    AsymmetricSignatureVerifier,
    TokenVerifier,
)
from channels.middleware import BaseMiddleware
from django.http import HttpRequest
from ninja.security import HttpBearer
from ninja.security.http import HttpAuthBase

import config.settings as settings
import base64

logger = logging.getLogger(__name__)

jwks_url = "https://{}/.well-known/jwks.json".format(settings.AUTH0_DOMAIN)
issuer = "https://{}/".format(settings.AUTH0_DOMAIN)

sv = AsymmetricSignatureVerifier(jwks_url)  # Reusable instance
tv = TokenVerifier(
    signature_verifier=sv, issuer=issuer, audience=settings.AUTH0_CLIENT_ID
)

DEFAULT_USER = "kubechat"


def get_user_from_token(token):
    if settings.AUTH_TYPE == "auth0":
        payload = tv.verify(token)
        user = payload["sub"]
    else:
        user = base64.b64decode(token).decode("ascii")
    return user


class GlobalHTTPAuth(HttpBearer):
    def authenticate(self, request, token):
        request.META["X-USER-ID"] = get_user_from_token(token)
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


class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, app):
        self.app = app

    def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])

        token = headers.get(b"sec-websocket-protocol", None)
        if token is not None:
            token = token.decode("ascii")
        scope["Sec-Websocket-Protocol"] = token
        scope["X-USER-ID"] = get_user_from_token(token)
        return self.app(scope, receive, send)
