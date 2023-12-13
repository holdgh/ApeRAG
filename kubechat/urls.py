from django.urls import path

from kubechat.views import main
from ninja import NinjaAPI
from ninja.errors import ValidationError, AuthenticationError

from kubechat.auth.validator import GlobalHTTPAuth
from kubechat.views.utils import validation_errors, auth_errors

from kubechat.views.config import router as config_router
from kubechat.views.main import router as main_router
from kubechat.views.feishu import router as feishu_router
from kubechat.views.weixin import router as weixin_router
from kubechat.views.web import router as web_router

api = NinjaAPI()
api.add_exception_handler(ValidationError, validation_errors)
api.add_exception_handler(AuthenticationError, auth_errors)

api.add_router("/", main_router, auth=GlobalHTTPAuth())
api.add_router("/", web_router)
api.add_router("/config", config_router)
api.add_router("/feishu", feishu_router)
api.add_router("/weixin", weixin_router)


urlpatterns = [
    path("v1/", api.urls),
    path('kubechat/dashboard/', main.dashboard, name='dashboard'),
]
