"""فیلترهای قالب برای نمایش تاریخ شمسی و ارقام فارسی."""

from django import template

from core.jalali import format_jalali, to_fa_digits

register = template.Library()


@register.filter(name="jalali")
def jalali(value):
    """تاریخ میلادی را به شمسی نمایش می‌دهد. مثال: «۱۷ شهریور ۱۴۰۴»."""
    return format_jalali(value)


@register.filter(name="jalali_full")
def jalali_full(value):
    """تاریخ شمسی همراه با نام روز هفته."""
    return format_jalali(value, with_day_name=True)


@register.filter(name="fa")
def fa(value):
    """ارقام لاتین را به فارسی تبدیل می‌کند."""
    return to_fa_digits(value)


@register.filter(name="absval")
def absval(value):
    """قدر مطلق عدد؛ برای نمایش «۲۸۰ روز گذشته» به جای «۲۸۰-»."""
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value
