from django.db import migrations


def set_oil_product(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    OilChange = apps.get_model("oilchange", "OilChange")
    oil = Product.objects.filter(slug="oil-change").first()
    if oil is None:
        return
    OilChange.objects.filter(product__isnull=True).update(product=oil)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("oilchange", "0002_oilchange_product"),
        ("catalog", "0002_seed_products"),
    ]

    operations = [
        migrations.RunPython(set_oil_product, noop),
    ]
