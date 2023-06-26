from django.urls import path

from . import views

from .views import api

urlpatterns = [
    path("v1/", api.urls),
]