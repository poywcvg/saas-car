"""عکس کاورِ مقاله‌های پیش‌فرض (عکس‌های Unsplash با لایسنس رایگان، در static/img/blog/)."""

from django.db import migrations

# اسلاگ → (فایل، متن جایگزین)
COVERS = {
    "هر-چند-وقت-روغن-موتور-عوض-کنیم": (
        "oil-refill.webp",
        "ریختن روغن موتور نو داخل موتور خودرو هنگام تعویض روغن",
    ),
    "راهنمای-انتخاب-روغن-موتور": (
        "motor-oil-shelf.webp",
        "قفسه‌ی روغن موتور با برندها و گرانروی‌های مختلف برای انتخاب روغن مناسب",
    ),
    "زمان-تعویض-فیلتر-روغن-و-هوا": (
        "oil-filter.webp",
        "دست مکانیک هنگام باز کردن فیلتر روغن خودرو",
    ),
    "چک-لیست-سرویس-دوره‌ای-خودرو": (
        "engine-inspection.webp",
        "مکانیک در حال بازدید موتور خودرو برای سرویس دوره‌ای",
    ),
    "باورهای-اشتباه-تعویض-روغن": (
        "motor-oil-bottles.webp",
        "چند ظرف روغن موتور و فیلتر روغن نو کنار خودرو",
    ),
    "آماده-سازی-خودرو-برای-سفر": (
        "road-trip.webp",
        "خودرو در جاده‌ی بین‌شهری؛ آماده‌سازی خودرو پیش از سفر",
    ),
    "روغن-موتور-مناسب-هوای-گرم-کرمان": (
        "desert-heat.webp",
        "خودرو در بیابانِ گرم و آفتابی؛ شرایطی مثل تابستان کرمان",
    ),
    "فیلتر-هوا-گرد-و-خاک-کرمان": (
        "air-filter.webp",
        "فیلتر هوای خودرو از نزدیک",
    ),
    "افزایش-مشتری-تعویض-روغنی": (
        "workshop.webp",
        "تعویض روغنی و تعمیرگاه مرتب با چند خودرو در حال سرویس",
    ),
    "نرم-افزار-تعویض-روغنی-چیست": (
        "mechanic-oil.webp",
        "مکانیک هنگام تعویض روغن موتور در تعویض روغنی",
    ),
}


def seed(apps, schema_editor):
    Post = apps.get_model("blog", "Post")
    for slug, (filename, alt) in COVERS.items():
        # فقط اگر ادمین قبلاً کاور دیگری نگذاشته باشد
        Post.objects.filter(slug=slug, cover="", cover_static="").update(
            cover_static=f"img/blog/{filename}", cover_alt=alt
        )


def unseed(apps, schema_editor):
    Post = apps.get_model("blog", "Post")
    for slug, (filename, _alt) in COVERS.items():
        Post.objects.filter(slug=slug, cover_static=f"img/blog/{filename}").update(
            cover_static="", cover_alt=""
        )


class Migration(migrations.Migration):
    dependencies = [("blog", "0005_post_cover")]

    operations = [migrations.RunPython(seed, unseed)]
