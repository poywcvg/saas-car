from django.conf import settings
from django.shortcuts import redirect, render

from apps.catalog.models import Product
from core import seo


# آیکون‌های SVG درون‌خطی (بدون وابستگی خارجی)
def _icon(path):
    return (
        '<svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round">{path}</svg>'
    )


HOME_CONTEXT = {
    # اعداد اعتمادساز (اعتماد اجتماعی)
    "stats": [
        {"value": "۳ برابر", "label": "شانس بازگشت مشتری"},
        {"value": "۵ دقیقه", "label": "زمان راه‌اندازی"},
        {"value": "۰", "label": "نیاز به دانش فنی"},
        {"value": "۲۴/۷", "label": "یادآوری خودکار"},
    ],
    # مزایا با قاب‌بندی نتیجه‌محور (فروش، وفاداری، اتوماسیون)
    "benefits": [
        {
            "title": "فروش بیشتر، بدون تبلیغات",
            "desc": "مشتری قدیمی سرِ موعد برمی‌گردد پیش تو، نه رقیب. هر یادآوری یعنی یک فروش دوباره.",
            "icon": _icon('<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/>'),
            "tone": "growth",
        },
        {
            "title": "باشگاه مشتریان وفادار",
            "desc": "همه‌ی مشتری‌ها و خودروهایشان یک‌جا، با تاریخچه‌ی کامل هر سرویس. رابطه‌ای که می‌ماند.",
            "icon": _icon('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>'),
            "tone": "brand",
        },
        {
            "title": "همه‌چیز خودکار",
            "desc": "موعد بعدی خودکار حساب می‌شود و پیامک یادآوری آماده می‌شود. تو فقط سرویس را بزن.",
            "icon": _icon('<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>'),
            "tone": "accent",
        },
    ],
    "steps": [
        {
            "title": "مشتری را ثبت کن",
            "desc": "اسم، شماره موبایل و خودرو را وارد کن. سرویس که انجام شد، تاریخ و کیلومتر را ثبت می‌کنی.",
            "icon": _icon('<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M19 8v6M22 11h-6"/>'),
        },
        {
            "title": "موعد بعدی خودکار حساب می‌شود",
            "desc": "سرویسا بر اساس کیلومتر و زمان، موعد سرویس بعدی را محاسبه می‌کند. لازم نیست چیزی به خاطر بسپاری.",
            "icon": _icon('<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>'),
        },
        {
            "title": "پیامک یادآوری می‌رود",
            "desc": "درست سرِ موعد، برای مشتری پیامک می‌رود و او را دعوت می‌کند برگردد پیش تو.",
            "icon": _icon('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'),
        },
    ],
}


def home(request):
    if request.user.is_authenticated:
        return redirect("businesses:dashboard")
    context = dict(HOME_CONTEXT)
    # صفحه‌ی معرفی فقط محصولات سراسریِ پلتفرم را نشان می‌دهد
    context["products"] = list(Product.objects.filter(business__isnull=True))
    # تازه‌ترین مقالات وبلاگ (تیزر + لینک داخلی برای سئو)
    from apps.blog.models import Post

    context["latest_posts"] = list(
        Post.published.select_related("category")[:3]
    )
    # داده‌ی ساختاریافته + لینک به صفحه‌های شهر (تا گوگل آن‌ها را بخزد)
    context["jsonld_org"] = seo.json_ld(seo.organization_ld())
    context["seo_cities"] = [
        {"name": c, "path": seo.city_page_path(c)} for c in settings.SEO_CITIES
    ]
    return render(request, "pages/home.html", context)
