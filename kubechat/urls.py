from django.urls import path
from ninja import NinjaAPI
from ninja.errors import AuthenticationError, ValidationError

from kubechat.auth.validator import GlobalHTTPAuth
from kubechat.utils.weixin.renderer import MyJSONRenderer
from kubechat.views import main
from kubechat.views.config import router as config_router
from kubechat.views.dingtalk import router as dingtalk_router
from kubechat.views.feishu import router as feishu_router
from kubechat.views.main import router as main_router
from kubechat.views.tencent import router as tencent_router
from kubechat.views.utils import auth_errors, validation_errors
from kubechat.views.web import router as web_router
from kubechat.views.weixin import router as weixin_router

api = NinjaAPI(renderer=MyJSONRenderer)
api.add_exception_handler(ValidationError, validation_errors)
api.add_exception_handler(AuthenticationError, auth_errors)

api.add_router("/", main_router, auth=GlobalHTTPAuth())
api.add_router("/", web_router)
api.add_router("/config", config_router)
api.add_router("/feishu", feishu_router)
api.add_router("/weixin", weixin_router)
api.add_router("/tencent", tencent_router)
api.add_router("/dingtalk", dingtalk_router)

urlpatterns = [
    path("v1/", api.urls),
    path('kubechat/dashboard/', main.dashboard, name='dashboard'),
]
