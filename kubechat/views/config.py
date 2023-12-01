from ninja import NinjaAPI, Router

from config import settings
from kubechat.views.utils import success

api = NinjaAPI(version="1.0.0", urls_namespace="config")

router = Router()


@router.get("")
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
