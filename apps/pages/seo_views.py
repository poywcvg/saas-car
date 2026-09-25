"""صفحه‌های سئو: فهرست تعویض روغنی‌های شهر، robots.txt و sitemap.xml."""

from urllib.parse import quote

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.text import slugify

from apps.businesses.models import Business
from core import seo


def _city_businesses(city):
    """تعویض روغنی‌های یک شهر که خودشان اجازه‌ی نمایش عمومی داده‌اند."""
    return list(
        Business.objects.filter(city__iexact=city, is_listed=True)
        .exclude(subdomain__isnull=True)
        .exclude(subdomain="")
        .order_by("name")
    )


def city_directory(request, city):
    """«تعویض روغنی در <شهر>» — صفحه‌ی فرود برای مشتری نهایی (B2C).

    کلمه‌ی کلیدی در URL، عنوان، H1 و داده‌ی ساختاریافته می‌نشیند؛ محتوا هم
    واقعاً مفید است (فهرست واقعی مغازه‌ها) نه متنِ پرشده از کلمه‌ی کلیدی.
    """
    # نامِ شهر را از فهرست شهرهای هدف پیدا کن (اسلاگ → نام فارسی)
    wanted = slugify(city, allow_unicode=True)
    city_name = next(
        (c for c in settings.SEO_CITIES if slugify(c, allow_unicode=True) == wanted),
        None,
    )
    if city_name is None:
        raise Http404("شهر پشتیبانی نمی‌شود.")

    businesses = _city_businesses(city_name)
    faqs = [
        (
            f"بهترین تعویض روغنی در {city_name} کجاست؟",
            f"در این صفحه فهرست تعویض روغنی‌های {city_name} که در سرویسا ثبت‌نام "
            "کرده‌اند آمده است. هر کدام صفحه‌ی اختصاصی، شماره تماس و سابقه‌ی "
            "سرویس آنلاین دارند تا بتوانید با خیال راحت انتخاب کنید.",
        ),
        (
            "هر چند وقت یک‌بار باید روغن موتور را عوض کرد؟",
            "بسته به نوع روغن و خودرو، معمولاً هر ۵۰۰۰ تا ۱۰۰۰۰ کیلومتر یا هر "
            "۶ ماه — هر کدام زودتر رسید. اگر سرویس خود را در سرویسا ثبت کنید، "
            "موعد بعدی خودکار حساب می‌شود و پیامک یادآوری دریافت می‌کنید.",
        ),
        (
            f"چطور سابقه‌ی تعویض روغن خودرویم را در {city_name} ببینم؟",
            "اگر تعویض روغنی شما از سرویسا استفاده می‌کند، پس از هر سرویس یک "
            "لینک پیامکی دریافت می‌کنید که تاریخ، کیلومتر، نوع روغن و موعد "
            "سرویس بعدی در آن ثبت است — بدون نیاز به نصب هیچ اپلیکیشنی.",
        ),
    ]

    return render(
        request,
        "pages/city_directory.html",
        {
            "city": city_name,
            "businesses": businesses,
            "faqs": faqs,
            "canonical": seo.absolute_url(seo.city_page_path(city_name)),
            "jsonld_list": seo.json_ld(seo.city_listing_ld(city_name, businesses)),
            "jsonld_faq": seo.json_ld(seo.faq_ld(faqs)),
            "jsonld_crumbs": seo.json_ld(
                seo.breadcrumb_ld(
                    [
                        ("سرویسا", "/"),
                        (f"تعویض روغنی در {city_name}", seo.city_page_path(city_name)),
                    ]
                )
            ),
        },
    )


def robots_txt(request):
    """به خزنده‌ها می‌گوید چه چیزی را نخزد و sitemap کجاست."""
    lines = [
        "User-agent: *",
        "Disallow: /accounts/",
        "Disallow: /businesses/",
        "Disallow: /customers/",
        "Disallow: /products/",
        "Disallow: /vehicles/",
        "Disallow: /garage/",
        "Disallow: /oilchange/",
        "Disallow: /orders/",
        "Disallow: /admin/",
        "Disallow: /c/",  # لینک خصوصی مشتری (پیامکی) نباید ایندکس شود
        "Allow: /",
        "Allow: /blog/",  # وبلاگ آموزشی؛ قلب تپنده‌ی سئوی محتوایی
        "",
        f"Sitemap: {seo.absolute_url('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    """نقشه‌ی سایتِ صفحه‌های عمومیِ پلتفرم + صفحه‌های شهر + وبلاگ.

    استاندارد sitemap نشانی را به شکل percent-encoded می‌خواهد؛ پس مسیرهای
    فارسی پیش از درج کدگذاری می‌شوند.
    """
    urls = [
        {"loc": seo.absolute_url("/"), "priority": "1.0", "changefreq": "weekly"},
        {"loc": seo.absolute_url("/blog/"), "priority": "0.8", "changefreq": "weekly"},
    ]
    for city in settings.SEO_CITIES:
        urls.append(
            {
                "loc": seo.absolute_url(quote(seo.city_page_path(city))),
                "priority": "0.9",
                "changefreq": "daily",
            }
        )

    # وبلاگ: دسته‌ها و مقالات منتشرشده با تاریخ آخرین ویرایش
    from apps.blog.models import Category, Post

    for category in Category.objects.order_by("sort_order", "id"):
        if not Post.published.filter(category=category).exists():
            continue
        urls.append(
            {
                "loc": seo.absolute_url(quote(category.get_absolute_url())),
                "priority": "0.7",
                "changefreq": "weekly",
            }
        )
    for post in Post.published.select_related("category"):
        updated = post.updated_at or post.published_at or post.created_at
        urls.append(
            {
                "loc": seo.absolute_url(quote(post.get_absolute_url())),
                "lastmod": updated.date().isoformat(),
                "priority": "0.8",
                "changefreq": "monthly",
            }
        )

    return render(
        request,
        "pages/sitemap.xml",
        {"urls": urls},
        content_type="application/xml; charset=utf-8",
    )
