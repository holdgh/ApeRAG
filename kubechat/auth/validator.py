import json
import config.settings as settings
from urllib.request import urlopen
from ninja.security import HttpBearer

from authlib.oauth2.rfc7523 import JWTBearerTokenValidator
from authlib.jose.rfc7517.jwk import JsonWebKey

# https://auth0.com/docs/quickstart/webapp/django/interactive#update-settings-py


class Auth0JWTBearerTokenValidator(JWTBearerTokenValidator):
    def __init__(self, domain, audience):
        issuer = f"https://{domain}/"
        jsonurl = urlopen(f"{issuer}.well-known/jwks.json")
        public_key = JsonWebKey.import_key_set(
            json.loads(jsonurl.read())
        )
        super(Auth0JWTBearerTokenValidator, self).__init__(
            public_key
        )
        self.claims_options = {
            "exp": {"essential": True},
            "aud": {"essential": True, "value": audience},
            "iss": {"essential": True, "value": issuer},
        }


class GlobalAuth(HttpBearer):
    def __init__(self):
        super().__init__()
        self.validator = Auth0JWTBearerTokenValidator(
            settings.AUTH0_DOMAIN,
            settings.AUTH0_CLIENT_ID,
        )

    def authenticate(self, request, token):
        self.validator.validate_token(token, "", request)
        claims = self.validator.authenticate_token(token)
        request.META["X-USER-ID"] = claims["sub"]


