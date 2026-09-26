"""تغییر نام برند «سرویسا» به «چرخیار» در محتوای ذخیره‌شده (مقالات و محصولات)."""

from django.db import migrations

OLD, NEW = "سرویسا", "چرخیار"


def _swap(value):
    """جایگزینی نام در رشته یا ساختارِ JSON (لیست/دیکشنری) به‌صورت بازگشتی."""
    if isinstance(value, str):
        return value.replace(OLD, NEW)
    if isinstance(value, list):
        return [_swap(v) for v in value]
    if isinstance(value, dict):
        return {k: _swap(v) for k, v in value.items()}
    return value


def _rebrand(model, fields):
    for obj in model.objects.all():
        dirty = []
        for f in fields:
            old = getattr(obj, f)
            new = _swap(old)
            if new != old:
                setattr(obj, f, new)
                dirty.append(f)
        if dirty:
            obj.save(update_fields=dirty)


def forwards(apps, schema_editor):
    _rebrand(
        apps.get_model("blog", "Post"),
        ["title", "excerpt", "content", "faqs", "meta_title", "meta_description"],
    )
    _rebrand(apps.get_model("blog", "Category"), ["title", "description"])
    _rebrand(apps.get_model("catalog", "Product"), ["title", "tagline", "description"])


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0002_seed_content"),
        ("catalog", "0005_refresh_product_icons"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
