from auth0.authentication.token_verifier import (
    AsymmetricSignatureVerifier,
    TokenVerifier,
)
from channels.middleware import BaseMiddleware
from ninja.security import HttpBearer

import config.settings as settings
import base64

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


class GlobalAuth(HttpBearer):
    def authenticate(self, request, token):
        request.META["X-USER-ID"] = get_user_from_token(token)
        return token


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
