from django.urls import path

from . import settings_views


app_name = "garage"


urlpatterns = [
    path("", settings_views.garage_settings, name="settings"),
]
