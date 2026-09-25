"""داده‌های پیش‌فرضِ لیست‌های خودرو و تابع seed برای هر کسب‌وکار.

هنگام ساخت یک کسب‌وکار (سیگنال post_save) و نیز برای کسب‌وکارهای موجود
(data migration) اجرا می‌شود تا owner از صفر شروع نکند.
"""

# برند → فهرست مدل‌ها (بازار ایران)
DEFAULT_BRANDS = {
    "ایران خودرو": [
        "پژو ۲۰۶", "پژو ۲۰۷", "پژو پارس", "پژو ۴۰۵", "سمند",
        "دنا", "رانا", "تارا", "سورن",
    ],
    "سایپا": [
        "پراید ۱۱۱", "پراید ۱۳۱", "پراید ۱۴۱", "تیبا", "تیبا ۲",
        "ساینا", "کوییک", "شاهین", "اطلس",
    ],
    "کیا": ["سراتو", "اسپورتیج", "ریو", "سِدونا", "اپتیما"],
    "هیوندای": ["اکسنت", "سوناتا", "توسان", "النترا", "i20"],
    "تویوتا": ["کرولا", "کمری", "یاریس", "پرادو", "هایلوکس"],
    "رنو": ["ال ۹۰ (تندر)", "ساندرو", "پارس تندر", "مگان"],
    "ام وی ام": ["ام وی ام ۳۱۵", "ام وی ام ۵۵۰", "ام وی ام X22", "ام وی ام X33"],
    "چری": ["آریزو ۵", "تیگو ۷", "تیگو ۸"],
    "جک": ["جک S3", "جک S5", "جک J4"],
    "بسترن": ["بسترن B30", "بسترن B50"],
}

DEFAULT_COLORS = [
    "سفید", "مشکی", "نقره‌ای", "خاکستری", "نوک‌ مدادی",
    "قرمز", "آبی", "سرمه‌ای", "بژ", "قهوه‌ای",
]

DEFAULT_OILS = [
    "بهران توربین ۲۰W۵۰", "ایرانول ۲۰W۵۰", "اسپیدی ۲۰W۵۰",
    "توتال ۵W۳۰", "شل ۱۰W۴۰", "کاسترول ۱۰W۴۰", "الف ۵W۴۰",
]

DEFAULT_FUELS = [
    "بنزین", "دوگانه‌سوز (CNG)", "دیزل (گازوئیل)", "هیبرید", "برقی",
]


def seed_business_defaults(business, *, brand_model=None, model_model=None,
                           option_model=None):
    """لیست‌های پیش‌فرض را برای یک کسب‌وکار می‌سازد (idempotent).

    مدل‌ها را می‌توان صریح پاس داد (برای استفاده در data migration با
    apps.get_model)؛ در غیر این صورت از مدل‌های واقعی import می‌شود.
    """
    if brand_model is None or model_model is None or option_model is None:
        from .models import VehicleBrand, VehicleModel, VehicleOption
        brand_model = brand_model or VehicleBrand
        model_model = model_model or VehicleModel
        option_model = option_model or VehicleOption

    for b_order, (brand_name, models) in enumerate(DEFAULT_BRANDS.items(), start=1):
        brand, _ = brand_model.objects.get_or_create(
            business=business,
            name=brand_name,
            defaults={"sort_order": b_order},
        )
        for m_order, model_name in enumerate(models, start=1):
            model_model.objects.get_or_create(
                brand=brand,
                name=model_name,
                defaults={"sort_order": m_order},
            )

    def _seed_options(kind, names):
        for order, name in enumerate(names, start=1):
            option_model.objects.get_or_create(
                business=business,
                kind=kind,
                name=name,
                defaults={"sort_order": order},
            )

    _seed_options("color", DEFAULT_COLORS)
    _seed_options("oil", DEFAULT_OILS)
    _seed_options("fuel", DEFAULT_FUELS)
