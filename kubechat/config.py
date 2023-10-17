from ninja import NinjaAPI

from config import settings
from kubechat.utils.request import success

api = NinjaAPI(version="1.0.0", urls_namespace="config")


@api.get("/config")
def config(request):
    auth = {
        "type": settings.AUTH_TYPE,
    }

    match settings.AUTH_TYPE:
        case "auth0":
            auth["auth_domain"] = settings.AUTH0_DOMAIN
            auth["auth_app_id"] = settings.AUTH0_CLIENT_ID
        case "authing":
            auth["auth_domain"] = settings.AUTHING_DOMAIN
            auth["auth_app_id"] = settings.AUTHING_APP_ID
    return success({"auth": auth})
