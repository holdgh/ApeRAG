from auth0.authentication.token_verifier import (
    AsymmetricSignatureVerifier,
    TokenVerifier,
)
from channels.middleware import BaseMiddleware
from ninja.security import HttpBearer

import config.settings as settings

jwks_url = "https://{}/.well-known/jwks.json".format(settings.AUTH0_DOMAIN)
issuer = "https://{}/".format(settings.AUTH0_DOMAIN)

sv = AsymmetricSignatureVerifier(jwks_url)  # Reusable instance
tv = TokenVerifier(
    signature_verifier=sv, issuer=issuer, audience=settings.AUTH0_CLIENT_ID
)

DEFAULT_USER = "kubechat"


def get_user_from_token(token):
    payload = tv.verify(token)
    return payload["sub"]


class GlobalAuth(HttpBearer):
    def authenticate(self, request, token):
        if settings.AUTH_ENABLED:
            request.META["X-USER-ID"] = get_user_from_token(token)
        else:
            request.META["X-USER-ID"] = DEFAULT_USER
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

        if settings.AUTH_ENABLED:
            scope["X-USER-ID"] = get_user_from_token(token)
        else:
            scope["X-USER-ID"] = DEFAULT_USER
        return self.app(scope, receive, send)
