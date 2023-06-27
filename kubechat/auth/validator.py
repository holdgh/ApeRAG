import config.settings as settings
from ninja.security import HttpBearer
from auth0.authentication.token_verifier import TokenVerifier, AsymmetricSignatureVerifier


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


class GlobalAuth(HttpBearer):
    def authenticate(self, request, token):
        # After authenticating
        jwks_url = 'https://{}/.well-known/jwks.json'.format(settings.AUTH0_DOMAIN)
        issuer = 'https://{}/'.format(settings.AUTH0_DOMAIN)

        sv = AsymmetricSignatureVerifier(jwks_url)  # Reusable instance
        tv = TokenVerifier(signature_verifier=sv, issuer=issuer, audience=settings.AUTH0_CLIENT_ID)
        payload = tv.verify(token)
        request.META["X-USER-ID"] = payload["sub"]
        return token
