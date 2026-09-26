"""کمک‌تابع‌های سئو: نشانی متعارف (canonical)، متای پیش‌فرض و داده‌ی ساختاریافته.

اصل کار: کلمه‌های کلیدی («تعویض روغنی»، نام شهر) در جایگاه‌های پرارزش
بنشینند — title، H1، meta description، URL و JSON-LD — نه با تکرارِ
بی‌رویه در متن که گوگل آن را keyword stuffing می‌شناسد و جریمه می‌کند.
"""

import json

from django.conf import settings
from django.urls import reverse
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


LOGO_PATH = "/static/img/logo.png"
OG_IMAGE_PATH = "/static/img/og-cover.png"


def social_links():
    """نشانی شبکه‌های اجتماعیِ پرشده (برای sameAs و فوتر)."""
    return {k: v for k, v in getattr(settings, "SOCIAL_LINKS", {}).items() if v}


def region_ld():
    """استان هدف به شکل AdministrativeArea."""
    return {
        "@type": "AdministrativeArea",
        "name": settings.SEO_REGION_NAME,
        "containedInPlace": {"@type": "Country", "name": "ایران"},
    }


def city_ld(city):
    """شهر به شکل City — با مختصات مرکز شهر و استانِ دربرگیرنده."""
    data = {"@type": "City", "name": city, "containedInPlace": region_ld()}
    geo = settings.SEO_CITY_GEO.get(city)
    if geo:
        data["geo"] = {"@type": "GeoCoordinates", "latitude": geo[0], "longitude": geo[1]}
    return data


def organization_ld():
    """داده‌ی ساختاریافته‌ی خودِ پلتفرم (برای صفحه‌ی اصلی).

    @id ثابت دارد تا WebSite و SoftwareApplication به همین سازمان ارجاع دهند
    و گوگل همه را یک «موجودیتِ برند» بشناسد (پایه‌ی Knowledge Panel).
    """
    data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": absolute_url("/#organization"),
        "name": settings.SITE_NAME,
        "alternateName": ["Charkhyar", "چرخ یار", "نرم‌افزار تعویض روغنی چرخیار"],
        "url": absolute_url("/"),
        "logo": {
            "@type": "ImageObject",
            "url": absolute_url(LOGO_PATH),
            "width": 512,
            "height": 512,
        },
        "image": absolute_url(OG_IMAGE_PATH),
        "slogan": "مشتری سرِ موعد برمی‌گردد",
        "description": (
            "چرخیار نرم‌افزار آنلاین تعویض روغنی و خدمات خودرو است: باشگاه "
            "مشتریان، سابقه‌ی سرویس هر خودرو و یادآوری خودکار پیامکی — ویژه‌ی "
            f"تعویض روغنی‌های {settings.SEO_PRIMARY_CITY} و {settings.SEO_REGION_NAME}."
        ),
        "areaServed": [city_ld(c) for c in settings.SEO_CITIES],
        "knowsAbout": ["تعویض روغن", "روغن موتور", "سرویس دوره‌ای خودرو", "باشگاه مشتریان"],
    }
    same_as = list(social_links().values())
    if same_as:
        data["sameAs"] = same_as
    return data


def website_ld():
    """WebSite + SearchAction — امکانِ جعبه‌ی جست‌وجو و شناخت نام برند در گوگل."""
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": absolute_url("/#website"),
        "name": settings.SITE_NAME,
        "alternateName": "Charkhyar",
        "url": absolute_url("/"),
        "inLanguage": "fa-IR",
        "publisher": {"@id": absolute_url("/#organization")},
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": absolute_url("/blog/") + "?q={search_term_string}",
            },
            "query-input": "required name=search_term_string",
        },
    }


def software_ld():
    """خودِ محصول (نرم‌افزار تعویض روغنی) با قیمت و دوره‌ی رایگان."""
    return {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": f"{settings.SITE_NAME} — نرم‌افزار تعویض روغنی",
        "applicationCategory": "BusinessApplication",
        "applicationSubCategory": "نرم‌افزار مدیریت تعویض روغنی و باشگاه مشتریان",
        "operatingSystem": "Web, Android, iOS",
        "inLanguage": "fa-IR",
        "url": absolute_url("/"),
        "image": absolute_url(OG_IMAGE_PATH),
        "publisher": {"@id": absolute_url("/#organization")},
        "description": (
            "ثبت مشتری و خودرو، سابقه‌ی کامل تعویض روغن، محاسبه‌ی خودکار موعد "
            "سرویس بعدی بر اساس کیلومتر و زمان و ارسال پیامک یادآوری."
        ),
        "featureList": [
            "ثبت نامحدود مشتری و خودرو",
            "سابقه‌ی کامل تعویض روغن و فیلتر",
            "محاسبه‌ی خودکار موعد سرویس بعدی",
            "یادآوری خودکار پیامکی",
            "سایت اختصاصی برای هر تعویض روغنی",
            "لینک پیامکی سابقه‌ی سرویس برای مشتری",
        ],
        "areaServed": [city_ld(c) for c in settings.SEO_CITIES],
        "offers": {
            "@type": "Offer",
            "price": str(settings.SEO_PRICE_MONTHLY_IRR),
            "priceCurrency": "IRR",
            "availability": "https://schema.org/InStock",
            "url": absolute_url(reverse("accounts:register", urlconf=settings.ROOT_URLCONF)),
            "description": "اشتراک ماهانه — ۷ روز اول رایگان، بدون کارت بانکی",
            "priceSpecification": {
                "@type": "UnitPriceSpecification",
                "price": str(settings.SEO_PRICE_MONTHLY_IRR),
                "priceCurrency": "IRR",
                "unitText": "ماه",
                "referenceQuantity": {
                    "@type": "QuantitativeValue",
                    "value": 1,
                    "unitCode": "MON",
                },
            },
        },
    }


def maps_url(business):
    """لینک نقشه‌ی کسب‌وکار (hasMap): مختصات اگر ثبت شده، وگرنه جست‌وجوی نشانی."""
    from urllib.parse import quote_plus

    if business.has_location:
        return f"https://www.google.com/maps/search/?api=1&query={business.latlng}"

    query = " ".join(p for p in (business.name, business.address, business.city) if p)
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"


def local_business_ld(business):
    """داده‌ی ساختاریافته‌ی یک تعویض روغنی — مبنای نتایج محلیِ گوگل.

    نوع AutoOilChange زیرمجموعه‌ی رسمی schema.org است و دقیقاً همان
    چیزی است که گوگل برای «تعویض روغنی نزدیک من» می‌فهمد.
    """
    url = business.tenant_url("/")
    data = {
        "@context": "https://schema.org",
        "@type": "AutoOilChange",
        "@id": f"{url}#business",
        "name": business.name,
        "url": url,
        "image": absolute_url(OG_IMAGE_PATH),
        "logo": absolute_url(LOGO_PATH),
        "priceRange": "$$",
        "currenciesAccepted": "IRR",
        "paymentAccepted": "نقد، کارت بانکی",
        "knowsAbout": ["تعویض روغن موتور", "تعویض فیلتر روغن", "تعویض فیلتر هوا"],
        "makesOffer": [
            {
                "@type": "Offer",
                "itemOffered": {"@type": "Service", "name": name},
            }
            for name in ("تعویض روغن موتور", "تعویض فیلتر روغن و هوا", "یادآوری پیامکی موعد سرویس")
        ],
    }
    if business.tagline:
        data["description"] = business.tagline
    else:
        data["description"] = (
            f"{business.name}، تعویض روغنی"
            + (f" در {business.city}" if business.city else "")
            + " — ثبت سابقه‌ی سرویس و یادآوری پیامکی موعد تعویض روغن بعدی."
        )
    if business.phone:
        data["telephone"] = business.phone

    address = {"@type": "PostalAddress", "addressCountry": "IR"}
    if business.city:
        address["addressLocality"] = business.city
        if business.city in settings.SEO_CITIES:
            address["addressRegion"] = settings.SEO_REGION_NAME
        data["areaServed"] = city_ld(business.city)
    if business.address:
        address["streetAddress"] = business.address
        data["hasMap"] = maps_url(business)
    if business.has_location:
        data["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": float(business.latitude),
            "longitude": float(business.longitude),
        }
        data["hasMap"] = maps_url(business)
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


def post_image(post):
    """تصویر مقاله برای سئو؛ بدون تصویر اختصاصی، لوگوی پلتفرم."""
    if getattr(post, "og_image", None):
        return post.og_image
    cover = getattr(post, "cover_url", "")
    if cover:
        return absolute_url(cover)
    return absolute_url(OG_IMAGE_PATH)


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
                "url": absolute_url(LOGO_PATH),
            },
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "image": [post_image(post)],
    }
    if published is not None:
        data["datePublished"] = published.isoformat()
    if updated is not None:
        data["dateModified"] = updated.isoformat()
    return data


def blog_index_ld(posts, url, name="وبلاگ چرخیار"):
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
    primary = settings.SEO_PRIMARY_CITY
    ctx = {
        "seo_site_name": settings.SITE_NAME,
        "seo_canonical": canonical_for(request),
        "seo_primary_city": primary,
        "seo_city_path": city_page_path(primary),
        "seo_og_image": absolute_url(OG_IMAGE_PATH),
        "seo_region_code": settings.SEO_REGION_CODE,
        "seo_geo_city": primary,
        "seo_geo": settings.SEO_CITY_GEO.get(primary),
        "seo_verify": {
            "google": settings.GOOGLE_SITE_VERIFICATION,
            "bing": settings.BING_SITE_VERIFICATION,
            "yandex": settings.YANDEX_SITE_VERIFICATION,
        },
        "seo_social": social_links(),
        # لینک‌های داخلیِ فوتر به صفحه‌های شهر (هر صفحه = یک لینک داخلی قوی)
        "seo_footer_cities": [
            {"name": c, "path": city_page_path(c)} for c in settings.SEO_CITIES
        ],
    }

    # روی سایتِ هر کسب‌وکار، داده‌ی ساختاریافته‌ی همان کسب‌وکار درج می‌شود.
    business = getattr(request, "business", None)
    if getattr(request, "is_tenant", False) and business is not None:
        ctx["seo_local_ld"] = json_ld(local_business_ld(business))
        if business.city:
            ctx["seo_geo_city"] = business.city
            ctx["seo_geo"] = settings.SEO_CITY_GEO.get(business.city)
        if business.has_location:
            ctx["seo_geo"] = (float(business.latitude), float(business.longitude))

    return ctx
