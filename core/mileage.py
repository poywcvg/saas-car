"""موتور محاسبهٔ حرفه‌ای کارکرد و موعد تعویض روغن.

منطق: کارکرد فعلی خودرو بین دو مراجعه نامعلوم است، پس از روی تاریخچهٔ
تعویض‌ها «میانگین کیلومتر روزانه» تخمین زده می‌شود. با این نرخ:
  • کارکرد تخمینیِ امروز محاسبه می‌شود،
  • تاریخی که خودرو به «کیلومتر موعد بعدی» می‌رسد پیش‌بینی می‌شود،
  • موعد مؤثر = زودترینِ (موعد تاریخی، موعد کیلومتری).

هیچ وابستگی خارجی ندارد و همهٔ ورودی‌ها می‌توانند None باشند.
"""

from __future__ import annotations

import datetime

# اگر تاریخچه‌ای برای تخمین نرخ نباشد، این نرخ پیش‌فرض به کار می‌رود
# (میانگین رانندگی روزمرهٔ یک خودروی شهری در ایران؛ محافظه‌کارانه)
DEFAULT_DAILY_KM = 45.0

# کف و سقف منطقی برای نرخ روزانه تا داده‌های پرت نتیجه را خراب نکنند
MIN_DAILY_KM = 5.0
MAX_DAILY_KM = 500.0


def _clamp_daily(value: float) -> float:
    return max(MIN_DAILY_KM, min(MAX_DAILY_KM, value))


def average_daily_km(oil_changes) -> float | None:
    """میانگین کیلومتر روزانه را از تاریخچهٔ تعویض‌ها تخمین می‌زند.

    ورودی: iterable از رکوردهای تعویض (هرکدام با service_date و mileage_km).
    خروجی: نرخ روزانه (float) یا None اگر داده کافی نباشد.

    از بازهٔ کاملِ قدیمی‌ترین تا تازه‌ترین رکورد استفاده می‌کند تا نوسان
    مراجعه‌های نزدیک‌به‌هم صاف شود.
    """
    points = [
        (oc.service_date, oc.mileage_km)
        for oc in oil_changes
        if oc.service_date is not None and oc.mileage_km is not None
    ]
    if len(points) < 2:
        return None

    points.sort(key=lambda p: (p[0], p[1]))
    first_date, first_km = points[0]
    last_date, last_km = points[-1]

    days = (last_date - first_date).days
    km = last_km - first_km
    if days <= 0 or km <= 0:
        return None

    return _clamp_daily(km / days)


def resolve_daily_km(oil_changes) -> float:
    """نرخ روزانهٔ قابل‌اتکا: تخمین از تاریخچه، وگرنه پیش‌فرض."""
    return average_daily_km(oil_changes) or DEFAULT_DAILY_KM


def estimate_current_mileage(
    last_mileage_km: int | None,
    last_service_date: datetime.date | None,
    daily_km: float | None,
    today: datetime.date | None = None,
) -> int | None:
    """کارکرد تخمینیِ خودرو در «امروز» را برمی‌گرداند."""
    if last_mileage_km is None or last_service_date is None:
        return None
    if today is None:
        today = datetime.date.today()
    rate = daily_km or DEFAULT_DAILY_KM
    elapsed = max(0, (today - last_service_date).days)
    return int(round(last_mileage_km + rate * elapsed))


def km_remaining(
    next_due_km: int | None,
    estimated_current_mileage: int | None,
) -> int | None:
    """چند کیلومتر تا موعد بعدی مانده (منفی یعنی گذشته)."""
    if next_due_km is None or estimated_current_mileage is None:
        return None
    return next_due_km - estimated_current_mileage


def projected_km_due_date(
    last_mileage_km: int | None,
    next_due_km: int | None,
    last_service_date: datetime.date | None,
    daily_km: float | None,
    today: datetime.date | None = None,
) -> datetime.date | None:
    """تاریخی که خودرو با نرخ فعلی به «کیلومتر موعد بعدی» می‌رسد."""
    if last_mileage_km is None or next_due_km is None or last_service_date is None:
        return None
    rate = daily_km or DEFAULT_DAILY_KM
    if rate <= 0:
        return None
    km_span = next_due_km - last_mileage_km
    if km_span <= 0:
        # همین حالا هم از کیلومتر رد شده‌ایم → موعد در روزِ آخرین تعویض
        return last_service_date
    days_needed = int(round(km_span / rate))
    return last_service_date + datetime.timedelta(days=days_needed)


def effective_due_date(
    date_due: datetime.date | None,
    km_due: datetime.date | None,
) -> datetime.date | None:
    """موعد مؤثر = زودترینِ موعد تاریخی و موعد کیلومتری."""
    candidates = [d for d in (date_due, km_due) if d is not None]
    if not candidates:
        return None
    return min(candidates)


def progress_percent(
    last_mileage_km: int | None,
    next_due_km: int | None,
    estimated_current_mileage: int | None,
) -> int | None:
    """درصد پیشرفت مصرفِ بازهٔ کیلومتری (۰ تا ۱۰۰+)."""
    if (
        last_mileage_km is None
        or next_due_km is None
        or estimated_current_mileage is None
    ):
        return None
    span = next_due_km - last_mileage_km
    if span <= 0:
        return 100
    used = estimated_current_mileage - last_mileage_km
    pct = int(round(used / span * 100))
    return max(0, min(100, pct))
