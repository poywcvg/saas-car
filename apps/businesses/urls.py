from django.urls import path

from . import views


app_name = "businesses"


urlpatterns = [
    path(
        "create/",
        views.create_business,
        name="create",
    ),

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "reminders/",
        views.reminders,
        name="reminders",
    ),
]