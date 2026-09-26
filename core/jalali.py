"""تبدیل تاریخ میلادی به شمسی (جلالی) — بدون وابستگی خارجی.

فقط برای نمایش استفاده می‌شود؛ داده‌ها در دیتابیس میلادی ذخیره می‌شوند.
"""

from __future__ import annotations

import datetime

MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]

WEEKDAYS = [
    "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه",
    "جمعه", "شنبه", "یکشنبه",
]  # ایندکس بر اساس datetime.weekday() (دوشنبه=۰)

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def to_fa_digits(value) -> str:
    """ارقام لاتین را به فارسی تبدیل می‌کند."""
    return str(value).translate(_FA_DIGITS)


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = (
        365 * gy
        + (gy2 + 3) // 4
        - (gy2 + 99) // 100
        + (gy2 + 399) // 400
        - 80
        + gd
        + g_d_m[gm - 1]
    )
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> tuple[int, int, int]:
    """تاریخ شمسی را به میلادی تبدیل می‌کند (الگوریتم استانداردِ jdf)."""
    jy += 1595
    days = -355668 + 365 * jy + (jy // 33) * 8 + ((jy % 33) + 3) // 4 + jd
    days += (jm - 1) * 31 if jm < 7 else (jm - 7) * 30 + 186
    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1
    leap = (gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0
    month_days = [0, 31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    for gm in range(1, 13):
        if gd <= month_days[gm]:
            break
        gd -= month_days[gm]
    return gy, gm, gd


def jalali_date(jy: int, jm: int, jd: int) -> datetime.date:
    """شمسی → datetime.date (ValueError اگر تاریخ نامعتبر باشد)."""
    if not (1 <= jm <= 12) or not (1 <= jd <= (31 if jm <= 6 else 30)):
        raise ValueError("invalid jalali date")
    date = datetime.date(*jalali_to_gregorian(jy, jm, jd))
    # روز ۳۰ اسفندِ سال غیرکبیسه به فروردین سال بعد می‌رود؛ رد کن
    if gregorian_to_jalali(date.year, date.month, date.day) != (jy, jm, jd):
        raise ValueError("invalid jalali date")
    return date


def _local_date(value):
    """datetime آگاه از منطقه‌ی زمانی را اول به وقت محلی (تهران) می‌برد، بعد تاریخش را می‌گیرد."""
    if isinstance(value, datetime.datetime):
        if value.tzinfo is not None:
            from django.utils import timezone

            value = timezone.localtime(value)
        return value.date()
    return value


def to_jalali(value) -> tuple[int, int, int]:
    """date → (سال، ماه، روز) شمسی."""
    value = _local_date(value)
    return gregorian_to_jalali(value.year, value.month, value.day)


def format_jalali(value, with_day_name: bool = False) -> str:
    """یک date/datetime را به رشته‌ی شمسی با ارقام فارسی تبدیل می‌کند.

    مثال خروجی: «۱۷ شهریور ۱۴۰۴» یا «سه‌شنبه ۱۷ شهریور ۱۴۰۴».
    """
    if value is None:
        return ""
    value = _local_date(value)
    jy, jm, jd = gregorian_to_jalali(value.year, value.month, value.day)
    text = f"{to_fa_digits(jd)} {MONTHS[jm - 1]} {to_fa_digits(jy)}"
    if with_day_name:
        text = f"{WEEKDAYS[value.weekday()]} {text}"
    return text
