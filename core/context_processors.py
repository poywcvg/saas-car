"""پردازنده‌های زمینه (context processors) مشترک برای همه‌ی صفحه‌ها."""

from django.db.models import Q

from apps.catalog.models import Product
from apps.vehicles.selectors import due_vehicles
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

    overdue, due_soon = due_vehicles(business)
    reminder_count = len(overdue) + len(due_soon)

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
