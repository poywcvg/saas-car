"""ارسال پیامک — در توسعه فقط در کنسول چاپ می‌شود.

بعداً با اتصال به یک درگاه پیامک واقعی (مثلاً کاوه‌نگار/ملی‌پیامک) جایگزین می‌شود.
"""

from __future__ import annotations

import logging

from core.jalali import format_jalali

logger = logging.getLogger("sms")


def build_reminder_text(customer, public_url: str, business_name: str = "") -> str:
    """متن پیامک یادآوری برای یک مشتری را می‌سازد."""
    lines = [f"سلام {customer.full_name} عزیز"]

    # نزدیک‌ترین خودرو به موعد را پیدا کن
    vehicles = [v for v in customer.vehicles.all() if v.next_due_date]
    vehicles.sort(key=lambda v: v.next_due_date)

    if vehicles:
        v = vehicles[0]
        # اطلاعات خودرو
        car_info = v.display_name
        if v.brand:
            car_info = v.brand.name
            if v.model:
                car_info += f" {v.model.name}"

        # کیلومتر فعلی و موعد بعدی
        mileage_info = ""
        if v.current_mileage_km:
            mileage_info = f"کارکرد فعلی: {v.current_mileage_km:,} کیلومتر"
        if v.next_due_km:
            km_diff = v.next_due_km - (v.current_mileage_km or 0)
            if km_diff > 0:
                mileage_info += f"\nتا تعویض بعدی: {km_diff:,} کیلومتر"

        lines.append(f"موعد تعویض روغن «{car_info}» نزدیکه.")
        if mileage_info:
            lines.append(mileage_info)
        lines.append(f"تاریخ موعد: {format_jalali(v.next_due_date)}")
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
