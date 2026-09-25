from django.db import migrations


PRODUCTS = [
    {
        "slug": "oil-change",
        "title": "تعویض روغن",
        "tagline": "یادآوری خودکار موعد بعدی و بازگشت مشتری",
        "description": "تاریخ و کیلومتر هر تعویض روغن ثبت می‌شود، موعد بعدی خودکار حساب "
        "می‌شود و درست سرِ وقت به مشتری پیامک یادآوری می‌رود.",
        "icon_svg": '<path d="M3 22h12"/><path d="M4 17h9V9H4z"/>'
        '<path d="M13 10h2.5L19 14v3h-6z"/>'
        '<path d="M6.5 9V6.5A1.5 1.5 0 0 1 8 5h3"/>'
        '<path d="M17.2 15.2s1.3 1.4 1.3 2.2a1.3 1.3 0 0 1-2.6 0c0-.8 1.3-2.2 1.3-2.2z"/>',
        "is_available": True,
        "is_flagship": True,
        "tracks_mileage": True,
        "default_interval_km": 5000,
        "default_interval_months": 3,
        "sort_order": 10,
    },
    {
        "slug": "filters",
        "title": "فیلتر روغن و هوا",
        "tagline": "پیگیری تعویض فیلترها کنار سرویس دوره‌ای",
        "description": "به‌زودی: مدیریت و یادآوری تعویض فیلتر روغن، هوا و کابین.",
        "icon_svg": '<path d="M4 4h16l-6 8v5l-4 2v-7z"/><path d="M7 7h10"/><path d="M9.5 10.5h5"/>',
        "is_available": False,
        "tracks_mileage": True,
        "default_interval_km": 10000,
        "default_interval_months": 6,
        "sort_order": 20,
    },
    {
        "slug": "battery",
        "title": "باتری و برق",
        "tagline": "کنترل عمر باتری و یادآوری تعویض",
        "description": "به‌زودی: ثبت تاریخ نصب باتری و هشدار پایان عمر مفید.",
        "icon_svg": '<rect x="2" y="8" width="16" height="9" rx="2"/>'
        '<path d="M18 11h2.5A1.5 1.5 0 0 1 22 12.5v1a1.5 1.5 0 0 1-1.5 1.5H18"/>'
        '<path d="M11 9.5 8.5 13H11l-1 3 4.5-4.5H12z"/>',
        "is_available": False,
        "tracks_mileage": False,
        "default_interval_km": 0,
        "default_interval_months": 24,
        "sort_order": 30,
    },
    {
        "slug": "tires",
        "title": "لاستیک و بالانس",
        "tagline": "یادآوری تعویض، جابه‌جایی و بالانس لاستیک",
        "description": "به‌زودی: پیگیری کارکرد لاستیک‌ها و زمان‌بندی بالانس و تنظیم باد.",
        "icon_svg": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="3"/>'
        '<path d="M12 3.5v2.5M12 18v2.5M3.5 12H6M18 12h2.5M6 6l1.8 1.8M16.2 16.2 18 18M18 6l-1.8 1.8M7.8 16.2 6 18"/>',
        "is_available": False,
        "tracks_mileage": True,
        "default_interval_km": 40000,
        "default_interval_months": 36,
        "sort_order": 40,
    },
    {
        "slug": "caver",
        "title": "سرامیک و کاور",
        "tagline": "باشگاه مشتریان کارواش و اشتراک شست‌وشو",
        "description": "به‌زودی: مدیریت اشتراک کارواش و یادآوری نوبت شست‌وشو.",
        "icon_svg": '<path d="M5 13l1.2-4.2A1.5 1.5 0 0 1 7.6 7.7h6.1a1.5 1.5 0 0 1 1.3.8L16.5 11H19v5h-2"/>'
        '<path d="M5 11h11"/><circle cx="8" cy="18" r="1.8"/><circle cx="16" cy="18" r="1.8"/>'
        '<path d="M10 18h4"/><path d="M18.5 3.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"/>',
        "is_available": False,
        "tracks_mileage": False,
        "default_interval_km": 0,
        "default_interval_months": 1,
        "sort_order": 50,
    },
]


def seed_products(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    for data in PRODUCTS:
        Product.objects.update_or_create(slug=data["slug"], defaults=data)


def unseed_products(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    Product.objects.filter(slug__in=[p["slug"] for p in PRODUCTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_products, unseed_products),
    ]
