"""آیکون‌های تازه و گویاتر برای محصولات (قابل‌فهم حتی بدون خواندن متن)."""

from django.db import migrations

# قطره‌ی روغن/آب — برای تکرار در چند آیکون
_DROP = 'c.6.9 1 1.5 1 2.1a1 1 0 0 1-2 0c0-.6.4-1.2 1-2.1z"/>'

ICONS = {
    # تعویض روغن: گالن روغن با لوله و قطره‌ی در حال چکیدن
    "oil-change": '<path d="M3.5 11.5h9.5l3.5 3.5v3a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 18z"/>'
    '<path d="M6.5 11.5V9.5h4v2"/><path d="M5.5 9.5h6"/><path d="M16.5 15l4-4"/>'
    '<path d="M6.5 15.5h5"/><path d="M20.5 14' + _DROP,
    # فیلتر: قوطی فیلتر روغن با شیارهای درپوش و قطره
    "filters": '<rect x="5" y="3" width="14" height="18" rx="3"/><path d="M5 8h14"/>'
    '<path d="M8.5 3v5M12 3v5M15.5 3v5"/>'
    '<path d="M12 11c.9 1.3 1.7 2.3 1.7 3.3a1.7 1.7 0 0 1-3.4 0c0-1 .8-2 1.7-3.3z"/>',
    # باتری خودرو: دو قطب مثبت و منفی
    "battery": '<rect x="2.5" y="7" width="19" height="13" rx="2"/>'
    '<path d="M5.5 7V4.5h3.5V7M15 7V4.5h3.5V7"/><path d="M6 13.5h3.5"/>'
    '<path d="M14.5 13.5H18M16.25 11.75v3.5"/>',
    # لاستیک: تایر + رینگ پنج‌پره
    "tires": '<circle cx="12" cy="12" r="9.5"/><circle cx="12" cy="12" r="5"/>'
    '<circle cx="12" cy="12" r="1.5"/>'
    '<path d="M12 10.5V7M13.43 11.54l3.33-1.09M12.88 13.21l2.06 2.84'
    'M11.12 13.21l-2.06 2.84M10.57 11.54 7.24 10.45"/>',
    # کارواش: خودرو زیر قطره‌های آب
    "carwash": '<path d="M3.5 18h-1v-3.2a1.5 1.5 0 0 1 1-1.4l2.5-.9 1.9-2.5a1.5 1.5 0 0 1 1.2-.6h5.3'
    'a1.5 1.5 0 0 1 1.1.5l2.3 2.5 2.7.9a1.5 1.5 0 0 1 1 1.4V18h-1"/>'
    '<circle cx="6.5" cy="18" r="2"/><circle cx="17.5" cy="18" r="2"/><path d="M8.5 18h7"/>'
    '<path d="M12 2.5' + _DROP + '<path d="M7 4' + _DROP + '<path d="M17 4' + _DROP,
}
ICONS["caver"] = ICONS["carwash"]


def update_icons(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    for slug, icon_svg in ICONS.items():
        # فقط محصولات سراسری پلتفرم؛ خدمات سفارشی کسب‌وکارها دست نمی‌خورد
        Product.objects.filter(business__isnull=True, slug=slug).update(icon_svg=icon_svg)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0004_update_product_icons"),
    ]

    operations = [
        migrations.RunPython(update_icons, noop),
    ]
