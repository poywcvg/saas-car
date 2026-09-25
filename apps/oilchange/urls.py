from django.urls import path

from . import views


app_name = "oilchange"


urlpatterns = [
    path("add/<int:vehicle_pk>/", views.oilchange_add, name="add"),
]
