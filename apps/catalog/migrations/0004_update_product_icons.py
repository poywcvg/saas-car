"""به‌روزرسانی آیکون‌های اختصاصی محصولات (لوگوی مرتبط با هر خدمت)."""

from django.db import migrations


ICONS = {
    # تعویض روغن: گالن روغن + قطره
    "oil-change": '<path d="M3 22h12"/><path d="M4 17h9V9H4z"/>'
    '<path d="M13 10h2.5L19 14v3h-6z"/>'
    '<path d="M6.5 9V6.5A1.5 1.5 0 0 1 8 5h3"/>'
    '<path d="M17.2 15.2s1.3 1.4 1.3 2.2a1.3 1.3 0 0 1-2.6 0c0-.8 1.3-2.2 1.3-2.2z"/>',
    # فیلتر: قیف + خطوط فیلتر
    "filters": '<path d="M4 4h16l-6 8v5l-4 2v-7z"/><path d="M7 7h10"/><path d="M9.5 10.5h5"/>',
    # باتری: بدنه + صاعقه
    "battery": '<rect x="2" y="8" width="16" height="9" rx="2"/>'
    '<path d="M18 11h2.5A1.5 1.5 0 0 1 22 12.5v1a1.5 1.5 0 0 1-1.5 1.5H18"/>'
    '<path d="M11 9.5 8.5 13H11l-1 3 4.5-4.5H12z"/>',
    # لاستیک: تایر + آج‌ها + رینگ
    "tires": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="3"/>'
    '<path d="M12 3.5v2.5M12 18v2.5M3.5 12H6M18 12h2.5M6 6l1.8 1.8M16.2 16.2 18 18M18 6l-1.8 1.8M7.8 16.2 6 18"/>',
    # سرامیک و کاور / کارواش: خودرو + برق سرامیک
    # (هر دو اسلاگ پوشش داده شده چون تغییرنام اسلاگ هنوز روی دیتابیس اعمال نشده)
    "caver": '<path d="M5 13l1.2-4.2A1.5 1.5 0 0 1 7.6 7.7h6.1a1.5 1.5 0 0 1 1.3.8L16.5 11H19v5h-2"/>'
    '<path d="M5 11h11"/><circle cx="8" cy="18" r="1.8"/><circle cx="16" cy="18" r="1.8"/>'
    '<path d="M10 18h4"/><path d="M18.5 3.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"/>',
    "carwash": '<path d="M5 13l1.2-4.2A1.5 1.5 0 0 1 7.6 7.7h6.1a1.5 1.5 0 0 1 1.3.8L16.5 11H19v5h-2"/>'
    '<path d="M5 11h11"/><circle cx="8" cy="18" r="1.8"/><circle cx="16" cy="18" r="1.8"/>'
    '<path d="M10 18h4"/><path d="M18.5 3.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"/>',
}


def update_icons(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    for slug, icon_svg in ICONS.items():
        # فقط محصولات سراسری پلتفرم؛ خدمات سفارشی کسب‌وکارها دست نمی‌خورد
        Product.objects.filter(business__isnull=True, slug=slug).update(icon_svg=icon_svg)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_product_business_alter_product_slug_and_more"),
    ]

    operations = [
        migrations.RunPython(update_icons, noop),
    ]
