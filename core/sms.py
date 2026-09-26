"""ارسال پیامک — در توسعه فقط در کنسول چاپ می‌شود.

بعداً با اتصال به یک درگاه پیامک واقعی (مثلاً کاوه‌نگار/ملی‌پیامک) جایگزین می‌شود.
"""

from __future__ import annotations

import logging

from core.jalali import format_jalali, to_fa_digits
from core.service_status import DUE_SOON_DAYS

logger = logging.getLogger("sms")


def build_reminder_text(customer, public_url: str, business_name: str = "") -> str:
    """متن پیامک یادآوری برای یک مشتری را می‌سازد."""
    lines = [f"سلام {customer.full_name} عزیز"]

    # نزدیک‌ترین خودرو به موعد (موعد مؤثر: تاریخی یا کیلومتری، هر کدام زودتر)
    vehicles = [v for v in customer.vehicles.all() if v.effective_due_date]
    vehicles.sort(key=lambda v: v.effective_due_date)

    if vehicles:
        v = vehicles[0]
        car_info = v.display_name or "خودروی شما"

        # کیلومتر تخمینیِ امروز و کیلومترِ مانده
        mileage_info = ""
        current_km = v.estimated_current_mileage or v.current_mileage_km
        if current_km:
            mileage_info = f"کارکرد حدودی: {current_km:,} کیلومتر"
        remaining = v.km_remaining
        if remaining is not None and remaining > 0:
            mileage_info += f"\nتا تعویض بعدی: {remaining:,} کیلومتر"

        days = v.days_until_due
        if days is not None and days < 0:
            lines.append(f"موعد تعویض روغن «{car_info}» گذشته است.")
        elif days is not None and days <= DUE_SOON_DAYS:
            lines.append(f"موعد تعویض روغن «{car_info}» نزدیکه.")
        else:
            lines.append(f"یادآوری تعویض روغن «{car_info}».")
        if mileage_info:
            lines.append(to_fa_digits(mileage_info.strip()))
        lines.append(f"تاریخ موعد: {format_jalali(v.effective_due_date)}")
    else:
        lines.append("یادآوری تعویض روغن خودروی شما.")

    lines.append("مشاهده جزئیات:")
    lines.append(public_url)
    if business_name:
        lines.append(f"— {business_name}")

    return "\n".join(lines)


def send_sms(phone: str, text: str) -> bool:
    """پیامک را «ارسال» می‌کند. فعلاً فقط در کنسول لاگ می‌شود."""
    banner = "=" * 42
    print(f"\n{banner}\nپیامک به {phone}\n{'-' * 42}\n{text}\n{banner}\n")
    logger.info("SMS to %s: %s", phone, text.replace("\n", " | "))
    return True
