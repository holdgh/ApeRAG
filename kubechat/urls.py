from django.urls import path

from kubechat.views import main, feishu, config, web

urlpatterns = [
    path("v1/", main.api.urls),
    path("v1/", web.api.urls),
    path("v1/", config.api.urls),
    path("v1/feishu/", feishu.api.urls),
    path('kubechat/dashboard/', main.dashboard, name='dashboard'),
]
