"""صفحه‌های سئو: فهرست تعویض روغنی‌های شهر، robots.txt و sitemap.xml."""


from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.encoding import iri_to_uri
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


def _city_indexable(city, businesses=None):
    """شهرِ اصلی همیشه؛ بقیه فقط وقتی دست‌کم یک تعویض روغنیِ عمومی دارند."""
    if city == settings.SEO_PRIMARY_CITY:
        return True
    if businesses is None:
        businesses = _city_businesses(city)
    return bool(businesses)


def _city_tips(city):
    """نکته‌های واقعاً مفیدِ محلی (نه متنِ پرشده از کلمه‌ی کلیدی).

    آب‌وهوای گرم و خشک و گرد و خاکِ استان کرمان روی روغن و فیلتر اثر مستقیم
    دارد؛ همین محتوای بومی است که صفحه را از رقبای سراسری متمایز می‌کند.
    """
    return [
        {
            "title": "تابستانِ گرم = روغن زودتر خسته می‌شود",
            "desc": (
                f"دمای بالای هوای {city} در تابستان و ترافیک شهری، روغن موتور را "
                "زودتر از حالت عادی رقیق می‌کند. اگر بیشتر در شهر رانندگی می‌کنید، "
                "موعد تعویض را کمی زودتر از عدد روی ظرف روغن در نظر بگیرید."
            ),
            "icon": '<path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/>',
            "tone": "accent",
        },
        {
            "title": "گرد و خاک = فیلتر هوا را جدی بگیرید",
            "desc": (
                f"جاده‌های بیابانی و بادهای پرگرد و خاکِ {settings.SEO_REGION_NAME}، فیلتر هوا "
                "را زود پر می‌کنند. با هر تعویض روغن، فیلتر هوا را هم چک کنید تا "
                "مصرف سوخت بالا نرود."
            ),
            "icon": '<path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/><path d="M17.5 8a2.5 2.5 0 1 1 2 4H2"/>',
            "tone": "brand",
        },
        {
            "title": "روغن با گرانروی مناسبِ هوای گرم",
            "desc": (
                "برای هوای گرم معمولاً روغن‌هایی مثل ۱۰W-40 یا ۵W-30 (بسته به "
                "دفترچه‌ی خودرو) مناسب‌اند. نوع روغنِ هر سرویس در سابقه‌ی آنلاینِ "
                "شما ثبت می‌شود تا دفعه‌ی بعد اشتباه نشود."
            ),
            "icon": '<path d="M12 2.7c2.6 3.4 5 6.3 5 9.3a5 5 0 0 1-10 0c0-3 2.4-5.9 5-9.3z"/>',
            "tone": "growth",
        },
    ]


def _city_faqs(city):
    """پرسش‌هایی که مشتری نهایی در گوگلِ شهرش می‌پرسد."""
    return [
        (
            f"بهترین تعویض روغنی در {city} کجاست؟",
            f"در این صفحه فهرست تعویض روغنی‌های {city} که در چرخیار ثبت‌نام "
            "کرده‌اند آمده است. هر کدام صفحه‌ی اختصاصی، شماره تماس، نشانی و "
            "سابقه‌ی سرویس آنلاین دارند تا بتوانید با خیال راحت انتخاب کنید.",
        ),
        (
            "هر چند وقت یک‌بار باید روغن موتور را عوض کرد؟",
            "بسته به نوع روغن و خودرو، معمولاً هر ۵۰۰۰ تا ۱۰۰۰۰ کیلومتر یا هر "
            "۶ ماه — هر کدام زودتر رسید. اگر سرویس خود را در چرخیار ثبت کنید، "
            "موعد بعدی خودکار حساب می‌شود و پیامک یادآوری دریافت می‌کنید.",
        ),
        (
            f"در هوای گرم {city} روغن موتور را زودتر عوض کنیم؟",
            "در رانندگی شهری، ترافیک و دمای بالای تابستان، بهتر است کمی زودتر از "
            "کیلومترِ پیشنهادیِ روغن اقدام کنید؛ به‌خصوص اگر خودرو قدیمی است یا "
            "زیاد در جاده‌های پرگرد و خاک رانندگی می‌کنید.",
        ),
        (
            "همراه تعویض روغن چه چیزهایی را باید چک کرد؟",
            "فیلتر روغن (معمولاً با هر تعویض)، فیلتر هوا، فیلتر کابین، سطح ضدیخ و "
            "روغن ترمز. در مناطق پرگرد و خاک، فیلتر هوا زودتر از حالت عادی کثیف می‌شود.",
        ),
        (
            f"چطور سابقه‌ی تعویض روغن خودرویم را در {city} ببینم؟",
            "اگر تعویض روغنی شما از چرخیار استفاده می‌کند، پس از هر سرویس یک "
            "لینک پیامکی دریافت می‌کنید که تاریخ، کیلومتر، نوع روغن و موعد "
            "سرویس بعدی در آن ثبت است — بدون نیاز به نصب هیچ اپلیکیشنی.",
        ),
        (
            f"تعویض روغنی دارم؛ چطور در این صفحه‌ی {city} دیده شوم؟",
            "کافی است در چرخیار ثبت‌نام کنید و شهرتان را وارد کنید. کسب‌وکار شما "
            "صفحه‌ی اختصاصی می‌گیرد و در فهرست تعویض روغنی‌های شهر نمایش داده "
            "می‌شود. ۷ روز اول رایگان است.",
        ),
    ]


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
    faqs = _city_faqs(city_name)
    nearby = [
        {"name": c, "path": seo.city_page_path(c)}
        for c in settings.SEO_CITIES
        if c != city_name
    ]

    return render(
        request,
        "pages/city_directory.html",
        {
            "city": city_name,
            "businesses": businesses,
            "faqs": faqs,
            "tips": _city_tips(city_name),
            "nearby": nearby,
            "region": settings.SEO_REGION_NAME,
            # صفحه‌ی خالیِ شهرهای فرعی «محتوای کم‌ارزش» است → noindex تا مغازه ثبت شود
            "indexable": _city_indexable(city_name, businesses),
            "canonical": seo.absolute_url(seo.city_page_path(city_name)),
            "jsonld_list": seo.json_ld(seo.city_listing_ld(city_name, businesses)),
            "jsonld_faq": seo.json_ld(seo.faq_ld(faqs)),
            "jsonld_crumbs": seo.json_ld(
                seo.breadcrumb_ld(
                    [
                        ("چرخیار", "/"),
                        (f"تعویض روغنی در {city_name}", seo.city_page_path(city_name)),
                    ]
                )
            ),
        },
    )


def tenant_robots_txt(request):
    """robots.txt سایتِ هر تعویض روغنی: پنل و لینک‌های خصوصی مشتری بسته‌اند."""
    lines = [
        "User-agent: *",
        "Disallow: /accounts/",
        "Disallow: /businesses/",
        "Disallow: /customers/",
        "Disallow: /products/",
        "Disallow: /vehicles/",
        "Disallow: /oilchange/",
        "Disallow: /c/",
        "Disallow: /lookup/?",  # نتیجه‌ی جست‌وجو = اطلاعات خصوصی مشتری
        "Allow: /",
        "",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def tenant_sitemap_xml(request):
    """sitemap سایتِ هر تعویض روغنی (ویترین + صفحه‌ی پیگیری)."""
    business = getattr(request, "business", None)
    if business is None or not business.is_listed:
        # کسب‌وکاری که نمایش عمومی را خاموش کرده، sitemap خالی می‌دهد
        urls = []
    else:
        lastmod = business.updated_at.date().isoformat() if business.updated_at else None
        urls = [
            {"loc": business.tenant_url("/"), "lastmod": lastmod,
             "priority": "1.0", "changefreq": "weekly"},
            {"loc": business.tenant_url("/lookup/"), "priority": "0.5",
             "changefreq": "monthly"},
        ]
    return render(
        request,
        "pages/sitemap.xml",
        {"urls": urls},
        content_type="application/xml; charset=utf-8",
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
        if not _city_indexable(city):
            continue  # صفحه‌ی noindex نباید در sitemap باشد
        urls.append(
            {
                "loc": seo.absolute_url(iri_to_uri(seo.city_page_path(city))),
                "priority": "0.9",
                "changefreq": "daily",
            }
        )

    # ویترینِ هر تعویض روغنیِ عمومی (ساب‌دامین) — صفحه‌ی اصلیِ سئوی B2C
    listed = (
        Business.objects.filter(is_listed=True)
        .exclude(subdomain__isnull=True)
        .exclude(subdomain="")
    )
    for b in listed:
        # دامنه‌ی اختصاصی، میزبانِ دیگری است؛ در sitemap خودش (tenant) می‌آید
        if b.custom_domain and not settings.DEBUG:
            continue
        entry = {"loc": b.tenant_url(), "priority": "0.8", "changefreq": "weekly"}
        if b.updated_at:
            entry["lastmod"] = b.updated_at.date().isoformat()
        urls.append(entry)

    # وبلاگ: دسته‌ها و مقالات منتشرشده با تاریخ آخرین ویرایش
    from apps.blog.models import Category, Post

    for category in Category.objects.order_by("sort_order", "id"):
        if not Post.published.filter(category=category).exists():
            continue
        urls.append(
            {
                "loc": seo.absolute_url(iri_to_uri(category.get_absolute_url())),
                "priority": "0.7",
                "changefreq": "weekly",
            }
        )
    for post in Post.published.select_related("category"):
        updated = post.updated_at or post.published_at or post.created_at
        urls.append(
            {
                "loc": seo.absolute_url(iri_to_uri(post.get_absolute_url())),
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
