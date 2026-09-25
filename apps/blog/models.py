"""مدل‌های وبلاگ سرویسا: دسته‌بندی، برچسب و مقاله.

سئو از همان ابتدا در مدل دیده شده: اسلاگ فارسی یکتا، متای اختصاصی هر
مقاله، چکیده، پرسش‌های متداول (برای FAQPage)، زمان مطالعه‌ی خودکار و
فهرست سرتیترها (برای TOC و لینک‌های داخلی صفحه).
"""

import re
from html import unescape

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

# تگ‌های سرفصل که از متن مقاله برای فهرست (TOC) استخراج می‌شوند
_HEADING_RE = re.compile(r"<(h[23])([^>]*)>(.*?)</\1>", re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _plain_text(html):
    """متن خالص یک رشته‌ی HTML (برای شمارش کلمات و توضیح خودکار)."""
    text = unescape(_TAG_RE.sub(" ", html or ""))
    return _WS_RE.sub(" ", text).strip()


class Category(models.Model):
    """دسته‌بندی مقالات، مثل «روغن موتور» یا «نگهداری خودرو»."""

    title = models.CharField(max_length=100, verbose_name="نام دسته")
    slug = models.SlugField(
        max_length=100,
        unique=True,
        allow_unicode=True,
        verbose_name="اسلاگ",
        help_text="فارسی و یکتا؛ در نشانی صفحه می‌آید، مثلاً: روغن-موتور",
    )
    description = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="توضیح کوتاه",
        help_text="در صفحه‌ی دسته و متای سئو استفاده می‌شود.",
    )
    icon_svg = models.TextField(
        blank=True,
        verbose_name="آیکون (مسیر SVG)",
        help_text="محتوای داخل تگ svg، مثلاً <path .../> — هماهنگ با آیکون‌های محصول.",
    )
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب نمایش")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:category", kwargs={"slug": self.slug})


class Tag(models.Model):
    """برچسب مقاله برای لینک‌سازی داخلی (فعلاً نمایشی/آینده‌نگر)."""

    title = models.CharField(max_length=60, verbose_name="نام برچسب")
    slug = models.SlugField(
        max_length=80, unique=True, allow_unicode=True, verbose_name="اسلاگ"
    )

    class Meta:
        ordering = ["title"]
        verbose_name = "برچسب"
        verbose_name_plural = "برچسب‌ها"

    def __str__(self):
        return self.title


class PublishedManager(models.Manager):
    """فقط مقالات منتشرشده‌ای که زمان انتشارشان رسیده است."""

    def get_queryset(self):
        now = timezone.now()
        return (
            super()
            .get_queryset()
            .filter(status=Post.Status.PUBLISHED)
            .filter(models.Q(published_at__isnull=True) | models.Q(published_at__lte=now))
        )


class Post(models.Model):
    """یک مقاله‌ی وبلاگ. محتوا HTML است و فقط از ادمین (کاربر مطمئن) می‌آید."""

    class Status(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        PUBLISHED = "published", "منتشرشده"

    title = models.CharField(max_length=160, verbose_name="عنوان مقاله")
    slug = models.SlugField(
        max_length=160,
        unique=True,
        allow_unicode=True,
        verbose_name="اسلاگ",
        help_text="فارسی و یکتا؛ کلمه‌ی کلیدی داخل نشانی، مثلاً: هر-چند-وقت-روغن-موتور",
    )
    excerpt = models.CharField(
        max_length=300,
        verbose_name="چکیده",
        help_text="در کارت‌ها، متای description و نتایج گوگل نمایش داده می‌شود.",
    )
    content = models.TextField(
        verbose_name="متن مقاله (HTML)",
        help_text="از h2 و h3 برای سرتیتر استفاده کن تا فهرست خودکار ساخته شود.",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="posts",
        verbose_name="دسته‌بندی",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts", verbose_name="برچسب‌ها")

    # پرسش‌های متداول انتهای مقاله → آکاردئون + FAQPage در JSON-LD
    faqs = models.JSONField(
        default=list,
        blank=True,
        verbose_name="پرسش‌های متداول",
        help_text='لیستی از {"q": "پرسش", "a": "پاسخ"}',
    )

    # --- سئوی اختصاصی (خالی = خودکار از عنوان و چکیده) ---
    meta_title = models.CharField(
        max_length=170, blank=True, verbose_name="عنوان سئو (meta title)"
    )
    meta_description = models.CharField(
        max_length=300, blank=True, verbose_name="توضیح سئو (meta description)"
    )
    og_image = models.URLField(
        blank=True,
        verbose_name="تصویر اشتراک‌گذاری (og:image)",
        help_text="خالی = لوگوی سرویسا.",
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="وضعیت",
    )
    published_at = models.DateTimeField(
        default=timezone.now,
        null=True,
        blank=True,
        verbose_name="زمان انتشار",
        help_text="پیش‌نویس‌ها منتشر نمی‌شوند؛ زمان آینده = انتشار زمان‌بندی‌شده.",
    )
    featured = models.BooleanField(default=False, verbose_name="ویژه (در صدر وبلاگ)")
    reading_minutes = models.PositiveSmallIntegerField(
        default=0, verbose_name="زمان مطالعه (دقیقه)"
    )
    views = models.PositiveIntegerField(default=0, verbose_name="بازدید")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["-published_at", "-id"]
        verbose_name = "مقاله"
        verbose_name_plural = "مقالات"
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:detail", kwargs={"slug": self.slug})

    # -- مشتق‌های سئو --

    @property
    def seo_title(self):
        return self.meta_title or self.title

    @property
    def seo_description(self):
        return self.meta_description or self.excerpt

    def save(self, *args, **kwargs):
        # زمان مطالعه: ~۲۰۰ کلمه در دقیقه برای فارسی
        words = len(_plain_text(self.content).split())
        self.reading_minutes = max(1, round(words / 200) or 1)
        super().save(*args, **kwargs)

    def headings(self):
        """سرتیترهای h2/h3 مقاله برای فهرست (TOC): [(سطح، متن، لنگر)]."""
        found = []
        for i, m in enumerate(_HEADING_RE.finditer(self.content or "")):
            level = int(m.group(1)[1])
            text = _plain_text(m.group(3))
            if text:
                found.append((level, text, f"h-{i}"))
        return found

    @property
    def content_with_anchors(self):
        """متن مقاله با id روی سرتیترها تا فهرست به آن‌ها لینک بدهد."""
        counter = {"i": 0}

        def _add_id(m):
            anchor = f"h-{counter['i']}"
            counter["i"] += 1
            attrs = m.group(2) or ""
            if re.search(r'\sid\s*=', attrs, re.IGNORECASE):
                return m.group(0)
            return f"<{m.group(1)}{attrs} id=\"{anchor}\">{m.group(3)}</{m.group(1)}>"

        return _HEADING_RE.sub(_add_id, self.content or "")

    def related_posts(self, limit=3):
        """مقالات مرتبط: اول هم‌دسته، بعد تازه‌ترین‌ها (برای لینک داخلی)."""
        qs = Post.published.exclude(pk=self.pk)
        same_cat = list(qs.filter(category=self.category)[:limit])
        if len(same_cat) < limit:
            seen = {p.pk for p in same_cat}
            for p in qs.exclude(pk__in=seen | {self.pk})[: limit - len(same_cat)]:
                same_cat.append(p)
        return same_cat

    def neighbors(self):
        """مقاله‌ی قبلی/بعدی بر اساس زمان انتشار (ناوبری انتهای مطلب)."""
        qs = Post.published.exclude(pk=self.pk)
        newer = qs.filter(
            models.Q(published_at__gt=self.published_at)
            | models.Q(published_at=self.published_at, id__gt=self.id)
        ).order_by("published_at", "id").first()
        older = qs.filter(
            models.Q(published_at__lt=self.published_at)
            | models.Q(published_at=self.published_at, id__lt=self.id)
        ).order_by("-published_at", "-id").first()
        return newer, older

    @staticmethod
    def anchor_slug(text, fallback):
        """متن سرتیتر → اسلاگ فارسی برای لنگر (در صورت نیاز آینده)."""
        return slugify(text, allow_unicode=True) or fallback
