from django.db import migrations

from apps.vehicles.defaults import seed_business_defaults


def seed_existing(apps, schema_editor):
    Business = apps.get_model("businesses", "Business")
    VehicleBrand = apps.get_model("vehicles", "VehicleBrand")
    VehicleModel = apps.get_model("vehicles", "VehicleModel")
    VehicleOption = apps.get_model("vehicles", "VehicleOption")
    for business in Business.objects.all():
        seed_business_defaults(
            business,
            brand_model=VehicleBrand,
            model_model=VehicleModel,
            option_model=VehicleOption,
        )


def unseed(apps, schema_editor):
    # لیست‌ها با حذف کسب‌وکار پاک می‌شوند؛ اینجا کاری لازم نیست.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("vehicles", "0004_vehiclebrand_vehiclemodel_vehicleoption_and_more"),
        ("businesses", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_existing, unseed),
    ]
