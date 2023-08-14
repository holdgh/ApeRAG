from django.urls import path

from . import views
from . import feishu

urlpatterns = [
    path("v1/", views.api.urls),
    path("v1/feishu/", feishu.api.urls),
    path('kubechat/dashboard/', views.dashboard, name='dashboard'),
]
