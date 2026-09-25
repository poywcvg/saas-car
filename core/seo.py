"""کمک‌تابع‌های سئو: نشانی متعارف (canonical)، متای پیش‌فرض و داده‌ی ساختاریافته.

اصل کار: کلمه‌های کلیدی («تعویض روغنی»، نام شهر) در جایگاه‌های پرارزش
بنشینند — title، H1، meta description، URL و JSON-LD — نه با تکرارِ
بی‌رویه در متن که گوگل آن را keyword stuffing می‌شناسد و جریمه می‌کند.
"""

import json

from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.text import slugify

# جلوگیری از بسته‌شدن زودهنگام تگ <script> یا تزریق اچ‌تی‌ام‌ال
_SCRIPT_ESCAPES = {
    ord("<"): "\\u003C",
    ord(">"): "\\u003E",
    ord("&"): "\\u0026",
}


def site_url():
    """ریشه‌ی نشانی متعارف سایت — در توسعه، میزبان محلی."""
    if settings.DEBUG:
        port = settings.TENANT_DEV_PORT
        host = settings.TENANT_DEV_BASE_DOMAIN
        return f"http://{host}:{port}" if port else f"http://{host}"
    return settings.SITE_URL


def absolute_url(path="/"):
    """نشانی مطلق از یک مسیر نسبی."""
    if path.startswith(("http://", "https://")):
        return path
    return f"{site_url()}{path if path.startswith('/') else '/' + path}"


def canonical_for(request):
    """نشانی متعارفِ همین درخواست، بدون کوئری‌استرینگ.

    روی ساب‌دامین نماینده، میزبانِ خودِ نماینده مبنا است تا صفحه‌ی هر
    کسب‌وکار canonical مستقل داشته باشد (نه اشاره به دامنه‌ی پلتفرم).
    """
    business = getattr(request, "business", None)
    if getattr(request, "is_tenant", False) and business is not None:
        return business.tenant_url(request.path)
    return absolute_url(request.path)


def city_slug(city):
    """نام شهر → اسلاگ فارسی برای URL."""
    return slugify(city, allow_unicode=True)


def city_page_path(city):
    """مسیر صفحه‌ی شهر؛ کلمه‌ی کلیدی داخل خودِ URL است (سیگنال قویِ سئو)."""
    return f"/تعویض-روغنی/{city_slug(city)}/"


def json_ld(data):
    """دیکشنری → تگ <script type="application/ld+json"> آماده‌ی درج.

    داخل <script> نباید از escape اچ‌تی‌ام‌ال استفاده کرد (مرورگر آن را باز
    نمی‌گرداند و JSON خراب می‌شود)؛ پس فقط نویسه‌های خطرناک به شکل \\uXXXX
    نوشته می‌شوند — همان کاری که خودِ جنگو در json_script می‌کند.
    """
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.translate(_SCRIPT_ESCAPES)
    return mark_safe(  # noqa: S308 — خروجی در بالا کاملاً امن شده است
        f'<script type="application/ld+json">{payload}</script>'
    )


def organization_ld():
    """داده‌ی ساختاریافته‌ی خودِ پلتفرم (برای صفحه‌ی اصلی)."""
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": settings.SITE_NAME,
        "url": absolute_url("/"),
        "logo": absolute_url("/static/img/logo.png"),
        "description": (
            "سرویسا نرم‌افزار مدیریت مشتری و یادآوری خودکار سرویس "
            "برای تعویض روغنی‌ها و کسب‌وکارهای خدمات خودرو است."
        ),
        "areaServed": {"@type": "City", "name": settings.SEO_PRIMARY_CITY},
    }


def local_business_ld(business):
    """داده‌ی ساختاریافته‌ی یک تعویض روغنی — مبنای نتایج محلیِ گوگل.

    نوع AutoOilChange زیرمجموعه‌ی رسمی schema.org است و دقیقاً همان
    چیزی است که گوگل برای «تعویض روغنی نزدیک من» می‌فهمد.
    """
    data = {
        "@context": "https://schema.org",
        "@type": "AutoOilChange",
        "name": business.name,
        "url": business.tenant_url("/"),
    }
    if business.tagline:
        data["description"] = business.tagline
    if business.phone:
        data["telephone"] = business.phone

    address = {"@type": "PostalAddress", "addressCountry": "IR"}
    if business.city:
        address["addressLocality"] = business.city
        data["areaServed"] = {"@type": "City", "name": business.city}
    if business.address:
        address["streetAddress"] = business.address
    if len(address) > 1:
        data["address"] = address

    return data


def city_listing_ld(city, businesses):
    """فهرستِ تعویض روغنی‌های یک شهر به‌صورت ItemList برای گوگل."""
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"تعویض روغنی‌های {city}",
        "numberOfItems": len(businesses),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "item": local_business_ld(b),
            }
            for i, b in enumerate(businesses, start=1)
        ],
    }


def faq_ld(pairs):
    """پرسش‌های متداول → FAQPage؛ در نتایج گوگل به شکل آکاردئون می‌آید.

    pairs: لیستی از (پرسش، پاسخ).
    """
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in pairs
        ],
    }


def breadcrumb_ld(items):
    """مسیر راهنما (breadcrumb) — در نتایج گوگل زیر عنوان نشان داده می‌شود.

    items: لیستی از (عنوان، مسیر).
    """
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "name": name,
                "item": absolute_url(path),
            }
            for i, (name, path) in enumerate(items, start=1)
        ],
    }


def _post_image(post):
    """تصویر مقاله برای سئو؛ بدون تصویر اختصاصی، لوگوی پلتفرم."""
    if getattr(post, "og_image", None):
        return post.og_image
    return absolute_url("/static/img/logo.png")


def blog_post_ld(post, url):
    """داده‌ی ساختاریافته‌ی یک مقاله (BlogPosting) برای rich result گوگل."""
    published = getattr(post, "published_at", None)
    updated = getattr(post, "updated_at", None) or published
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post.title,
        "description": post.seo_description,
        "inLanguage": "fa-IR",
        "author": {
            "@type": "Organization",
            "name": settings.SITE_NAME,
            "url": absolute_url("/"),
        },
        "publisher": {
            "@type": "Organization",
            "name": settings.SITE_NAME,
            "logo": {
                "@type": "ImageObject",
                "url": absolute_url("/static/img/logo.png"),
            },
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "image": [_post_image(post)],
    }
    if published is not None:
        data["datePublished"] = published.isoformat()
    if updated is not None:
        data["dateModified"] = updated.isoformat()
    return data


def blog_index_ld(posts, url, name="وبلاگ سرویسا"):
    """داده‌ی ساختاریافته‌ی صفحه‌ی اصلی وبلاگ (Blog + فهرست مقالات)."""
    return {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": name,
        "inLanguage": "fa-IR",
        "url": url,
        "blogPost": [
            {
                "@type": "BlogPosting",
                "headline": p.title,
                "description": p.seo_description,
                "url": absolute_url(p.get_absolute_url()),
            }
            for p in posts
        ],
    }


def seo_defaults(request):
    """context processor: مقادیر پیش‌فرضِ سئو برای همه‌ی قالب‌ها."""
    ctx = {
        "seo_site_name": settings.SITE_NAME,
        "seo_canonical": canonical_for(request),
        "seo_primary_city": settings.SEO_PRIMARY_CITY,
        "seo_city_path": city_page_path(settings.SEO_PRIMARY_CITY),
    }

    # روی سایتِ هر کسب‌وکار، داده‌ی ساختاریافته‌ی همان کسب‌وکار درج می‌شود.
    business = getattr(request, "business", None)
    if getattr(request, "is_tenant", False) and business is not None:
        ctx["seo_local_ld"] = json_ld(local_business_ld(business))

    return ctx
