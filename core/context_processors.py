"""پردازنده‌های زمینه (context processors) مشترک برای همه‌ی صفحه‌ها."""

import datetime

from django.db.models import Q

from apps.catalog.models import Product
from apps.vehicles.models import Vehicle
from core import service_status
from core.access import current_business, user_role_in


def nav_badges(request):
    """داده‌های ناوبری کناری: نام کسب‌وکار و تعداد خودروهای نیازمند یادآوری.

    روی همه‌ی صفحه‌های کاربرِ واردشده در دسترس است تا نشان (badge) کنار
    «یادآوری‌ها» در ساید‌بار نمایش داده شود.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    business = current_business(request)
    if not business:
        return {}

    today = datetime.date.today()
    soon = today + datetime.timedelta(days=service_status.DUE_SOON_DAYS)
    reminder_count = Vehicle.objects.filter(
        customer__business=business,
        next_due_date__isnull=False,
        next_due_date__lte=soon,
    ).count()

    return {
        "nav_business": business,
        "nav_role": user_role_in(user, business),
        "nav_reminder_count": reminder_count,
        "nav_products": list(
            Product.objects.filter(is_available=True).filter(
                Q(business__isnull=True) | Q(business=business)
            )
        ),
    }
