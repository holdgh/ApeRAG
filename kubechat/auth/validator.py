import config.settings as settings
from ninja.security import HttpBearer
from auth0.authentication.token_verifier import TokenVerifier, AsymmetricSignatureVerifier
from channels.middleware import BaseMiddleware


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


'''
class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, app, inner):
        # Store the ASGI application we were passed
        super().__init__(inner)
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            query_string = dict(parse_qsl(scope["query_string"].decode("utf-8")))
            token = query_string["token"]

            scope["user"] = await get_user_from_token(token)
            return await self.app(scope, receive, send)
        except (KeyError, ValueError) as e:
            if isinstance(e, KeyError):
                error_msg = "Token not provided."
            else:
                error_msg = "Invalid token."

            # Add this line to set an error message in the scope
            scope["error_msg"] = error_msg
            await send(
                {"type": "websocket.close", "code": 1000, "reason": "Invalid token."}
            )

            return await self.app(scope, receive, send)

    @classmethod
    def get_token_auth_header(cls, request):
        """Obtains the Access Token from the Authorization Header
        """
        auth = request.headers.get("Authorization", None)
        if not auth:
            raise AuthError({"code": "authorization_header_missing",
                             "description":
                                 "Authorization header is expected"}, 401)

        parts = auth.split()

        if parts[0].lower() != "bearer":
            raise AuthError({"code": "invalid_header",
                             "description":
                                 "Authorization header must start with"
                                 " Bearer"}, 401)
        elif len(parts) == 1:
            raise AuthError({"code": "invalid_header",
                             "description": "Token not found"}, 401)
        elif len(parts) > 2:
            raise AuthError({"code": "invalid_header",
                             "description":
                                 "Authorization header must be"
                                 " Bearer token"}, 401)

        return parts[1]
'''