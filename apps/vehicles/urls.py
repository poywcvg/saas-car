from django.urls import path

from . import views


app_name = "vehicles"


urlpatterns = [
    path("add/<int:customer_pk>/", views.vehicle_add, name="add"),
    path("<int:pk>/", views.vehicle_detail, name="detail"),
    path("<int:pk>/edit/", views.vehicle_edit, name="edit"),
]
