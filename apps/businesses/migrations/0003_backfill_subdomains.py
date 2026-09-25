from django.db import migrations
from django.utils.text import slugify


def gen_subdomain(Business, business, taken):
    base = slugify(business.name)
    if len(base) < 3:
        base = "shop"
    base = base[:28]
    candidate = base
    n = 1
    while candidate in taken:
        n += 1
        candidate = f"{base}-{n}"
    return candidate


def forwards(apps, schema_editor):
    Business = apps.get_model("businesses", "Business")
    taken = set(
        Business.objects.exclude(subdomain__isnull=True)
        .exclude(subdomain="")
        .values_list("subdomain", flat=True)
    )
    for business in Business.objects.filter(subdomain__isnull=True).order_by("pk"):
        sub = gen_subdomain(Business, business, taken)
        taken.add(sub)
        business.subdomain = sub
        business.save(update_fields=["subdomain"])


def backwards(apps, schema_editor):
    # برگشت‌پذیری امن نیست؛ کاری نمی‌کنیم.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("businesses", "0002_business_address_business_custom_domain_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
