from django.urls import path

from . import views


app_name = "orders"


urlpatterns = [
    path("", views.order_list, name="list"),
    path("<int:pk>/", views.order_detail, name="detail"),
    path("new/<int:product_id>/", views.order_create, name="create"),
]
