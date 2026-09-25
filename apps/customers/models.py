import uuid

from django.db import models

from core import service_status


class Customer(models.Model):
    business = models.ForeignKey(
        "businesses.Business",
        on_delete=models.CASCADE,
        related_name="customers",
        verbose_name="کسب‌وکار",
    )

    full_name = models.CharField(
        max_length=120,
        verbose_name="نام مشتری",
    )

    phone = models.CharField(
        max_length=15,
        verbose_name="شماره موبایل",
    )

    note = models.CharField(
        max_length=250,
        blank=True,
        verbose_name="یادداشت",
    )

    # شناسه‌ی عمومی برای لینک پیامکی مشتری (بدون نیاز به ورود)
    public_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        verbose_name="شناسه‌ی لینک",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "مشتری"
        verbose_name_plural = "مشتریان"

    def __str__(self):
        return self.full_name

    @property
    def status(self):
        """بدترین وضعیت میان خودروهای مشتری."""
        priority = {
            service_status.OVERDUE: 3,
            service_status.DUE_SOON: 2,
            service_status.OK: 1,
            service_status.NONE: 0,
        }
        worst = service_status.NONE
        for vehicle in self.vehicles.all():
            if priority[vehicle.status] > priority[worst]:
                worst = vehicle.status
        return worst

    @property
    def status_meta(self):
        return service_status.STATUS_META[self.status]
