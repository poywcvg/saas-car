"""منطق مشترک وضعیت سرویس (سالم / نزدیک موعد / گذشته)."""

from __future__ import annotations

import datetime
from django.utils import timezone

# چند روز مانده به موعد، «نزدیک موعد» حساب شود
DUE_SOON_DAYS = 14

# کلیدهای وضعیت
NONE = "none"
OK = "ok"
DUE_SOON = "due_soon"
OVERDUE = "overdue"

# برچسب فارسی و کلاس نشان برای هر وضعیت
STATUS_META = {
    NONE: {"label": "بدون سابقه", "badge": "badge-neutral", "dot": "bg-slate-400"},
    OK: {"label": "سالم", "badge": "badge-ok", "dot": "bg-ok"},
    DUE_SOON: {"label": "نزدیک موعد", "badge": "badge-warn badge-pulse", "dot": "bg-warn"},
    OVERDUE: {"label": "گذشته از موعد", "badge": "badge-danger badge-pulse", "dot": "bg-danger"},
}


def compute_status(next_due_date, today: datetime.date | None = None) -> str:
    """وضعیت را از روی تاریخ موعد بعدی حساب می‌کند."""
    if next_due_date is None:
        return NONE
    if today is None:
        today = timezone.localdate()
    if next_due_date < today:
        return OVERDUE
    if next_due_date <= today + datetime.timedelta(days=DUE_SOON_DAYS):
        return DUE_SOON
    return OK


def days_until(next_due_date, today: datetime.date | None = None) -> int | None:
    """چند روز تا موعد بعدی مانده (منفی یعنی گذشته)."""
    if next_due_date is None:
        return None
    if today is None:
        today = timezone.localdate()
    return (next_due_date - today).days
