"""نرمال‌سازی ورودی‌های فارسی: تبدیل ارقام فارسی/عربی به انگلیسی و ..."""

# ۰۱۲۳۴۵۶۷۸۹ (فارسی) و ٠١٢٣٤٥٦٧٨٩ (عربی) → 0123456789
_DIGIT_MAP = {ord(c): str(i % 10) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩")}


def to_ascii_digits(value: str) -> str:
    return (value or "").translate(_DIGIT_MAP)


def digits_only(value: str) -> str:
    """فقط رقم‌ها را نگه می‌دارد (پس از تبدیل ارقام فارسی)."""
    return "".join(ch for ch in to_ascii_digits(value) if ch.isdigit())


def normalize_phone(value: str) -> str:
    """
    شماره موبایل را برای مقایسه یکدست می‌کند.
    ۰۹۱۲... / 0912... / +98912... / 98912... → 0912...
    """
    d = digits_only(value)
    if d.startswith("0098"):
        d = d[4:]
    if d.startswith("98") and len(d) == 12:
        d = d[2:]
    if len(d) == 10 and d.startswith("9"):
        d = "0" + d
    return d


def normalize_plate(value: str) -> str:
    """پلاک را برای مقایسه یکدست می‌کند: فقط رقم‌ها (حروف و جداکننده حذف)."""
    return digits_only(value)
