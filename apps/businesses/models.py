from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils.text import slugify

subdomain_validator = RegexValidator(
    regex=r"^[a-z0-9]([a-z0-9-]{1,30}[a-z0-9])$",
    message="ساب‌دامین فقط حروف انگلیسی کوچک، عدد و خط تیره (۳ تا ۳۲ نویسه).",
)


class Business(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name="نام کسب‌وکار",
    )

    # نشانی اختصاصی روی چرخیار: <subdomain>.charkhyar.ir
    subdomain = models.SlugField(
        max_length=32,
        unique=True,
        null=True,
        blank=True,
        validators=[subdomain_validator],
        verbose_name="ساب‌دامین",
        help_text="نشانی سایت شما: نام‌شما.charkhyar.ir",
    )

    # دامنه‌ی اختصاصی کسب‌وکار (اختیاری، برای بعد): shop-domain.com
    custom_domain = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        verbose_name="دامنه‌ی اختصاصی",
    )

    # توضیح کوتاه برای ویترین عمومی
    tagline = models.CharField(
        max_length=160,
        blank=True,
        verbose_name="شعار / توضیح کوتاه",
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="شماره تماس",
    )

    address = models.CharField(
        max_length=250,
        blank=True,
        verbose_name="نشانی",
    )

    # شهر — پایه‌ی سئوی محلی (صفحه‌ی «تعویض روغنی در کرمان»)
    city = models.CharField(
        max_length=60,
        blank=True,
        db_index=True,
        verbose_name="شهر",
        help_text="برای دیده‌شدن در جست‌وجوی محلی گوگل، مثلاً: کرمان",
    )

    # لوکیشن روی نقشه — مشتری با یک دکمه مسیر مغازه را پیدا می‌کند.
    # فقط کسب‌وکاری که محصولی خریده می‌تواند ثبتش کند (has_purchase).
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="عرض جغرافیایی",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="طول جغرافیایی",
    )

    # اجازه‌ی نمایش در فهرست عمومیِ شهر (صاحب کسب‌وکار می‌تواند خاموش کند)
    is_listed = models.BooleanField(
        default=True,
        verbose_name="نمایش در فهرست عمومی چرخیار",
        help_text="اگر خاموش باشد، در صفحه‌ی شهر نمایش داده نمی‌شود.",
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_businesses",
        verbose_name="مالک",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی",
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.subdomain:
            self.subdomain = self._generate_subdomain()
        super().save(*args, **kwargs)

    def _generate_subdomain(self):
        """یک ساب‌دامین یکتا و ASCII بساز (از روی نام، وگرنه shop<n>)."""
        base = slugify(self.name)  # نام فارسی → معمولاً خالی
        if len(base) < 3:
            base = "shop"
        base = base[:28]
        candidate = base
        n = 1
        qs = Business.objects.all()
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        while qs.filter(subdomain=candidate).exists():
            n += 1
            candidate = f"{base}-{n}"
        return candidate

    @property
    def city_slug(self):
        """شهر به شکل اسلاگ فارسی برای URL — مثلاً «بندر عباس» → «بندر-عباس»."""
        return slugify(self.city, allow_unicode=True)

    @property
    def has_location(self):
        return self.latitude is not None and self.longitude is not None

    @property
    def has_purchase(self):
        """آیا این کسب‌وکار محصولی سفارش داده (لغونشده)؟ شرطِ ثبت لوکیشن."""
        return self.orders.exclude(status="cancelled").exists()

    @property
    def latlng(self):
        """«lat,lng» با نقطه‌ی انگلیسی برای لینک‌های نقشه."""
        if not self.has_location:
            return ""
        return f"{float(self.latitude):.6f},{float(self.longitude):.6f}"

    @property
    def directions_urls(self):
        """لینک مسیریابی در اپ‌های نقشه‌ی رایج در ایران (به ترتیب محبوبیت)."""
        if not self.has_location:
            return []
        lat = f"{float(self.latitude):.6f}"
        lng = f"{float(self.longitude):.6f}"
        return [
            {"key": "neshan", "label": "نشان", "url": f"https://neshan.org/maps/@{lat},{lng},17z,0p"},
            {"key": "balad", "label": "بلد", "url": f"https://balad.ir/location?latitude={lat}&longitude={lng}&zoom=17"},
            {"key": "google", "label": "گوگل‌مپ", "url": f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"},
        ]

    @property
    def primary_host(self):
        """میزبان اصلی این کسب‌وکار (دامنه‌ی اختصاصی یا ساب‌دامین چرخیار)."""
        if self.custom_domain:
            return self.custom_domain
        return f"{self.subdomain}.{settings.TENANT_BASE_DOMAIN}"

    def tenant_url(self, path="/"):
        """نشانی کاملِ سایتِ نماینده؛ در توسعه از *.localhost استفاده می‌کند."""
        if self.custom_domain and not settings.DEBUG:
            return f"https://{self.custom_domain}{path}"

        if settings.DEBUG:
            host = f"{self.subdomain}.{settings.TENANT_DEV_BASE_DOMAIN}"
            if settings.TENANT_DEV_PORT:
                host = f"{host}:{settings.TENANT_DEV_PORT}"
            return f"http://{host}{path}"

        return f"https://{self.primary_host}{path}"


class Membership(models.Model):

    class Role(models.TextChoices):
        OWNER = "owner", "مالک"
        MANAGER = "manager", "مدیر"
        EMPLOYEE = "employee", "کارمند"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="کاربر",
    )

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="کسب‌وکار",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        verbose_name="نقش",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ عضویت",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "business"],
                name="unique_user_business_membership",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.business} - {self.role}"