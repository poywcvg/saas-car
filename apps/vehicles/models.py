from django.db import models

from core import mileage, service_status


class VehicleBrand(models.Model):
    """برند خودرو — مخصوص هر کسب‌وکار (owner مدیریت می‌کند)."""

    business = models.ForeignKey(
        "businesses.Business",
        on_delete=models.CASCADE,
        related_name="vehicle_brands",
        verbose_name="کسب‌وکار",
    )
    name = models.CharField(max_length=60, verbose_name="برند")
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "برند خودرو"
        verbose_name_plural = "برندهای خودرو"
        constraints = [
            models.UniqueConstraint(
                fields=["business", "name"],
                name="unique_brand_per_business",
            )
        ]

    def __str__(self):
        return self.name


class VehicleModel(models.Model):
    """مدل خودرو، زیرمجموعه‌ی یک برند."""

    brand = models.ForeignKey(
        VehicleBrand,
        on_delete=models.CASCADE,
        related_name="models",
        verbose_name="برند",
    )
    name = models.CharField(max_length=60, verbose_name="مدل")
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "مدل خودرو"
        verbose_name_plural = "مدل‌های خودرو"
        constraints = [
            models.UniqueConstraint(
                fields=["brand", "name"],
                name="unique_model_per_brand",
            )
        ]

    def __str__(self):
        return f"{self.brand.name} {self.name}"


class VehicleOption(models.Model):
    """گزینه‌های ساده و قابل‌مدیریتِ خودرو (رنگ، نوع روغن، نوع سوخت)."""

    class Kind(models.TextChoices):
        COLOR = "color", "رنگ"
        OIL = "oil", "نوع روغن"
        FUEL = "fuel", "نوع سوخت"

    business = models.ForeignKey(
        "businesses.Business",
        on_delete=models.CASCADE,
        related_name="vehicle_options",
        verbose_name="کسب‌وکار",
    )
    kind = models.CharField(
        max_length=10,
        choices=Kind.choices,
        db_index=True,
        verbose_name="نوع گزینه",
    )
    name = models.CharField(max_length=80, verbose_name="عنوان")
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        ordering = ["kind", "sort_order", "name"]
        verbose_name = "گزینه‌ی خودرو"
        verbose_name_plural = "گزینه‌های خودرو"
        constraints = [
            models.UniqueConstraint(
                fields=["business", "kind", "name"],
                name="unique_option_per_business_kind",
            )
        ]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.name}"


class Vehicle(models.Model):
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.CASCADE,
        related_name="vehicles",
        verbose_name="مشتری",
    )

    title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="خودرو",
        help_text="مثلاً: پژو ۲۰۶ سفید",
    )

    # مشخصات ساختاری (اختیاری — با لیست‌های قابل‌مدیریتِ کسب‌وکار)
    brand = models.ForeignKey(
        VehicleBrand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicles",
        verbose_name="برند",
    )
    model = models.ForeignKey(
        VehicleModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicles",
        verbose_name="مدل",
    )
    year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="سال ساخت",
    )
    color = models.ForeignKey(
        VehicleOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicles_with_color",
        limit_choices_to={"kind": VehicleOption.Kind.COLOR},
        verbose_name="رنگ",
    )
    fuel = models.ForeignKey(
        VehicleOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicles_with_fuel",
        limit_choices_to={"kind": VehicleOption.Kind.FUEL},
        verbose_name="نوع سوخت",
    )

    plate = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="پلاک",
    )

    current_mileage_km = models.PositiveIntegerField(
        default=0,
        verbose_name="کیلومتر فعلی",
        help_text="کارکرد فعلی خودرو بر اساس کیلومترشمار.",
    )

    # تنظیمات سرویسِ مخصوص این خودرو (پیش‌فرضِ ثبت تعویض روغن)
    service_interval_km = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="فاصله سرویس (کیلومتر)",
        help_text="اگر خالی بماند، از آخرین تعویض یا پیش‌فرض استفاده می‌شود.",
    )
    service_interval_months = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="فاصله سرویس (ماه)",
    )
    preferred_oil = models.ForeignKey(
        VehicleOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicles_with_oil",
        limit_choices_to={"kind": VehicleOption.Kind.OIL},
        verbose_name="روغن پیشنهادی",
    )

    # مقادیر denormalize‌شده از آخرین تعویض روغن، برای نمایش و آمار سریع
    last_service_date = models.DateField(
        null=True, blank=True, verbose_name="تاریخ آخرین تعویض"
    )
    last_mileage_km = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="کارکرد در آخرین تعویض"
    )
    last_oil_name = models.CharField(
        max_length=100, blank=True, verbose_name="روغن آخر"
    )
    next_due_date = models.DateField(
        null=True, blank=True, db_index=True, verbose_name="موعد بعدی"
    )
    next_due_km = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="کیلومتر موعد بعدی"
    )
    # میانگین کیلومتر روزانه (تخمین‌زده از تاریخچه)، برای پیش‌بینی موعد
    avg_daily_km = models.FloatField(
        null=True, blank=True, verbose_name="میانگین کیلومتر روزانه"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "خودرو"
        verbose_name_plural = "خودروها"

    def __str__(self):
        return self.display_name

    def compose_title(self):
        """عنوان را از مشخصات ساختاری می‌سازد (برند مدل رنگ)."""
        parts = []
        if self.brand_id:
            parts.append(self.brand.name)
        if self.model_id:
            parts.append(self.model.name)
        if self.color_id:
            parts.append(self.color.name)
        return " ".join(parts).strip()

    @property
    def display_name(self):
        """نام نمایشی: از مشخصات ساختاری، وگرنه عنوان دستی."""
        return self.compose_title() or self.title

    def save(self, *args, **kwargs):
        # عنوان را با مشخصات ساختاری همگام نگه‌دار تا کدهای قدیمیِ .title کار کنند
        composed = self.compose_title()
        if composed:
            self.title = composed
        super().save(*args, **kwargs)

    @property
    def latest_oilchange(self):
        return self.oil_changes.order_by("-service_date", "-id").first()

    # ---- محاسبات کارکرد (کیلومتر) ----

    @property
    def daily_km(self):
        """نرخ روزانهٔ قابل‌اتکا: تخمینِ ذخیره‌شده یا پیش‌فرض."""
        return self.avg_daily_km or mileage.DEFAULT_DAILY_KM

    @property
    def estimated_current_mileage(self):
        """کارکرد تخمینیِ خودرو در امروز."""
        return mileage.estimate_current_mileage(
            self.last_mileage_km, self.last_service_date, self.avg_daily_km
        )

    @property
    def km_remaining(self):
        """کیلومتر ماندهٔ تا موعد بعدی (منفی = گذشته)."""
        return mileage.km_remaining(
            self.next_due_km, self.estimated_current_mileage
        )

    @property
    def projected_due_date(self):
        """تاریخ پیش‌بینی‌شدهٔ رسیدن به کیلومتر موعد بعدی."""
        return mileage.projected_km_due_date(
            self.last_mileage_km,
            self.next_due_km,
            self.last_service_date,
            self.avg_daily_km,
        )

    @property
    def effective_due_date(self):
        """موعد مؤثر: زودترینِ موعد تاریخی و موعد کیلومتری."""
        return mileage.effective_due_date(
            self.next_due_date, self.projected_due_date
        )

    @property
    def km_progress_percent(self):
        """درصد مصرفِ بازهٔ کیلومتری تا تعویض بعدی."""
        return mileage.progress_percent(
            self.last_mileage_km,
            self.next_due_km,
            self.estimated_current_mileage,
        )

    # ---- وضعیت سرویس (بر پایهٔ موعد مؤثر) ----

    @property
    def status(self):
        return service_status.compute_status(self.effective_due_date)

    @property
    def status_meta(self):
        return service_status.STATUS_META[self.status]

    @property
    def days_until_due(self):
        return service_status.days_until(self.effective_due_date)

    @property
    def due_reason(self):
        """کدام معیار موعد را تعیین کرده: «km» یا «date» یا None."""
        date_due = self.next_due_date
        km_due = self.projected_due_date
        if km_due is None and date_due is None:
            return None
        if km_due is None:
            return "date"
        if date_due is None:
            return "km"
        return "km" if km_due <= date_due else "date"

    def refresh_service_status(self):
        """مقادیر خلاصه را از روی آخرین تعویض روغن بروزرسانی و ذخیره می‌کند."""
        latest = self.latest_oilchange
        if latest is None:
            self.last_service_date = None
            self.last_mileage_km = None
            self.last_oil_name = ""
            self.next_due_date = None
            self.next_due_km = None
            self.avg_daily_km = None
        else:
            self.last_service_date = latest.service_date
            self.last_mileage_km = latest.mileage_km
            self.last_oil_name = latest.oil_name
            self.next_due_date = latest.next_due_date
            self.next_due_km = latest.next_due_km
            # نرخ روزانه را از کل تاریخچه تخمین بزن (None اگر داده کم باشد)
            self.avg_daily_km = mileage.average_daily_km(self.oil_changes.all())
        self.save(
            update_fields=[
                "last_service_date",
                "last_mileage_km",
                "last_oil_name",
                "next_due_date",
                "next_due_km",
                "avg_daily_km",
                "updated_at",
            ]
        )
