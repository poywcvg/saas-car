import datetime

from django.conf import settings
from django.db import models


def _add_months(base: datetime.date, months: int) -> datetime.date:
    """چند ماه به یک تاریخ اضافه می‌کند (بدون وابستگی خارجی)."""
    month_index = base.month - 1 + months
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    # روز را در صورت کوتاه‌بودن ماه مقصد، محدود می‌کنیم
    day = min(base.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
                         else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return datetime.date(year, month, day)


class OilChange(models.Model):
    """یک رکورد تعویض روغن برای یک خودرو."""

    # بازه‌های پیش‌فرض متداول برای تعویض روغن
    INTERVAL_KM_CHOICES = [
        (3000, "۳٬۰۰۰ کیلومتر"),
        (5000, "۵٬۰۰۰ کیلومتر"),
        (7000, "۷٬۰۰۰ کیلومتر"),
        (8000, "۸٬۰۰۰ کیلومتر"),
        (10000, "۱۰٬۰۰۰ کیلومتر"),
    ]
    INTERVAL_MONTHS_CHOICES = [
        (2, "۲ ماه"),
        (3, "۳ ماه"),
        (4, "۴ ماه"),
        (6, "۶ ماه"),
        (12, "۱۲ ماه"),
    ]

    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="oil_changes",
        verbose_name="خودرو",
    )

    # محصولی که این رکورد به آن مربوط است (پیش‌فرض: تعویض روغن)
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="records",
        null=True,
        blank=True,
        verbose_name="محصول",
    )

    service_date = models.DateField(
        default=datetime.date.today,
        verbose_name="تاریخ تعویض",
    )

    mileage_km = models.PositiveIntegerField(
        verbose_name="کیلومتر (کارکرد)",
    )

    oil_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="نوع روغن",
        help_text="اختیاری، مثلاً: بهران توربین ۲۰W۵۰",
    )

    interval_km = models.PositiveIntegerField(
        default=5000,
        verbose_name="فاصله تا تعویض بعدی (کیلومتر)",
    )

    interval_months = models.PositiveIntegerField(
        default=3,
        verbose_name="فاصله تا تعویض بعدی (ماه)",
    )

    # محاسبه‌شده هنگام ذخیره
    next_due_km = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="کیلومتر موعد بعدی"
    )
    next_due_date = models.DateField(
        null=True, blank=True, verbose_name="تاریخ موعد بعدی"
    )

    note = models.CharField(
        max_length=250, blank=True, verbose_name="یادداشت"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="oil_changes",
        verbose_name="ثبت‌کننده",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت")

    class Meta:
        ordering = ["-service_date", "-id"]
        verbose_name = "تعویض روغن"
        verbose_name_plural = "تعویض روغن‌ها"

    def __str__(self):
        return f"{self.vehicle} — {self.service_date}"

    def save(self, *args, **kwargs):
        # موعد بعدی را همیشه از روی مقادیر فعلی حساب کن
        self.next_due_km = self.mileage_km + self.interval_km
        self.next_due_date = _add_months(self.service_date, self.interval_months)
        super().save(*args, **kwargs)
