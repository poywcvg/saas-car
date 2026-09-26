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

    # لوکیشن مغازه روی نقشه (برای خریداران محصول)
    path(
        "location/",
        views.business_location,
        name="location",
    ),

    # ثبت سریع تعویض روغن: جست‌وجو با موبایل/پلاک/اسم
    path(
        "quick/",
        views.quick_service,
        name="quick",
    ),
]