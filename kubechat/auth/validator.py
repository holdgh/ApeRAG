import config.settings as settings
from urllib.parse import parse_qsl
from ninja.security import HttpBearer
from auth0.authentication.token_verifier import TokenVerifier, AsymmetricSignatureVerifier
from channels.middleware import BaseMiddleware


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def get_user_from_token(token):
    jwks_url = 'https://{}/.well-known/jwks.json'.format(settings.AUTH0_DOMAIN)
    issuer = 'https://{}/'.format(settings.AUTH0_DOMAIN)

    sv = AsymmetricSignatureVerifier(jwks_url)  # Reusable instance
    tv = TokenVerifier(signature_verifier=sv, issuer=issuer, audience=settings.AUTH0_CLIENT_ID)
    payload = tv.verify(token)
    return payload["sub"]


class GlobalAuth(HttpBearer):
    def authenticate(self, request, token):
        request.META["X-USER-ID"] = get_user_from_token(token)
        return token


class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, app, inner):
        # Store the ASGI application we were passed
        super().__init__(inner)
        self.app = app

    def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        token = headers['Sec-Websocket-Protocol']
        scope["user"] = get_user_from_token(token)
        return self.app(scope, receive, send)