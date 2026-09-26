from django.db import models


class Product(models.Model):
    """یک محصول/خدمت قابل‌ارائه در پلتفرم خدمات خودرو.

    «تعویض روغن» محصول پرچم‌دار و فعال است؛ بقیه‌ی محصولات به‌تدریج فعال می‌شوند.
    هر رکورد خدمت (مثل OilChange) به یکی از این محصولات وصل می‌شود.

    اگر business خالی باشد، محصولِ سراسریِ پلتفرم است؛ در غیر این صورت
    خدمتِ سفارشیِ همان کسب‌وکار است که صاحبش تعریف کرده.
    """

    business = models.ForeignKey(
        "businesses.Business",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="کسب‌وکار",
        help_text="خالی = محصول سراسری پلتفرم.",
    )

    title = models.CharField(
        max_length=100,
        verbose_name="نام محصول",
    )

    slug = models.SlugField(
        max_length=100,
        allow_unicode=True,
        verbose_name="شناسه (slug)",
    )

    tagline = models.CharField(
        max_length=160,
        blank=True,
        verbose_name="توضیح یک‌خطی",
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    # مسیر SVG درون‌خطی (بدون تگ <svg>)، هماهنگ با آیکون‌های موجود
    icon_svg = models.TextField(
        blank=True,
        verbose_name="آیکون (مسیر SVG)",
        help_text="محتوای داخل تگ svg، مثلاً <path .../>",
    )

    is_available = models.BooleanField(
        default=False,
        verbose_name="فعال است",
        help_text="اگر خاموش باشد، محصول به‌صورت «به‌زودی» نمایش داده می‌شود.",
    )

    is_flagship = models.BooleanField(
        default=False,
        verbose_name="محصول پرچم‌دار",
    )

    # پیش‌فرض‌های زمان‌بندی سرویس (برای محصولات دوره‌ای مثل تعویض روغن)
    tracks_mileage = models.BooleanField(
        default=True,
        verbose_name="بر اساس کارکرد (کیلومتر)",
    )
    default_interval_km = models.PositiveIntegerField(
        default=5000,
        verbose_name="فاصله پیش‌فرض (کیلومتر)",
    )
    default_interval_months = models.PositiveIntegerField(
        default=3,
        verbose_name="فاصله پیش‌فرض (ماه)",
    )

    sort_order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="ترتیب نمایش",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        constraints = [
            models.UniqueConstraint(
                fields=["business", "slug"],
                name="unique_product_slug_per_business",
            )
        ]

    def __str__(self):
        return self.title

    # رنگ ثابت هر خدمت تا کاربر محصول را از رنگ لوگو هم بشناسد
    TONES = {
        "oil-change": "amber",
        "filters": "green",
        "battery": "blue",
        "tires": "slate",
        "carwash": "sky",
        "caver": "sky",
    }

    @property
    def tone(self):
        """نام رنگ لوگوی محصول (برای کلاس pack-logo-*)؛ پیش‌فرض رنگ برند."""
        return self.TONES.get(self.slug, "brand")

    @property
    def is_custom(self):
        """آیا این محصول را خودِ کسب‌وکار تعریف کرده (نه سراسری)."""
        return self.business_id is not None
