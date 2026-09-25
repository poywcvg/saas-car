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


def format_jalali(value, with_day_name: bool = False) -> str:
    """یک date/datetime را به رشته‌ی شمسی با ارقام فارسی تبدیل می‌کند.

    مثال خروجی: «۱۷ شهریور ۱۴۰۴» یا «سه‌شنبه ۱۷ شهریور ۱۴۰۴».
    """
    if value is None:
        return ""
    if isinstance(value, datetime.datetime):
        value = value.date()
    jy, jm, jd = gregorian_to_jalali(value.year, value.month, value.day)
    text = f"{to_fa_digits(jd)} {MONTHS[jm - 1]} {to_fa_digits(jy)}"
    if with_day_name:
        text = f"{WEEKDAYS[value.weekday()]} {text}"
    return text
