from django.urls import path

from . import views

app_name = "tenants"

urlpatterns = [
    path("", views.storefront, name="storefront"),
    path("lookup/", views.lookup, name="lookup"),
]
