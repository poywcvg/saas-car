"""پرس‌وجوهای مشترکِ «کدام خودروها به یادآوری نیاز دارند».

وضعیتِ هر خودرو (سالم/نزدیک موعد/گذشته) بر پایه‌ی «موعد مؤثر» است: زودترینِ
موعد تاریخی و موعد کیلومتری (Vehicle.effective_due_date). موعد کیلومتری از
کارکرد روزانه‌ی تخمینی حساب می‌شود و در دیتابیس ذخیره نیست، پس فیلترِ SQL روی
next_due_date به‌تنهایی خودروهایی را که «از نظر کیلومتر» سررسیده‌اند جا می‌اندازد.
همه‌ی صفحه‌ها (داشبورد، یادآوری‌ها، نشانِ منو و پیامک خودکار) از همین‌جا
می‌خوانند تا عددها و رنگ‌ها همه‌جا یکی باشند.
"""

from __future__ import annotations

import datetime

from core import service_status

from .models import Vehicle
from django.utils import timezone


def due_vehicles(business=None, days: int = service_status.DUE_SOON_DAYS):
    """خودروهای گذشته از موعد یا نزدیک موعد، مرتب بر اساس فوریت.

    خروجی: (overdue, due_soon) — دو فهرست از Vehicle.
    business=None یعنی همه‌ی کسب‌وکارها (برای فرمان پیامک).
    """
    today = timezone.localdate()
    cutoff = today + datetime.timedelta(days=days)

    qs = Vehicle.objects.filter(last_service_date__isnull=False).select_related(
        "customer", "customer__business"
    )
    if business is not None:
        qs = qs.filter(customer__business=business)

    overdue, due_soon = [], []
    for vehicle in qs:
        due = vehicle.effective_due_date
        if due is None or due > cutoff:
            continue
        (overdue if due < today else due_soon).append(vehicle)

    overdue.sort(key=lambda v: v.effective_due_date)
    due_soon.sort(key=lambda v: v.effective_due_date)
    return overdue, due_soon
