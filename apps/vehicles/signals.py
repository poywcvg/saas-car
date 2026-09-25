"""سیگنال‌های اپ خودروها."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.businesses.models import Business

from .defaults import seed_business_defaults


@receiver(post_save, sender=Business, dispatch_uid="seed_vehicle_defaults")
def seed_defaults_for_new_business(sender, instance, created, **kwargs):
    """با ساخت هر کسب‌وکار، لیست‌های پیش‌فرضِ خودرو را می‌سازد."""
    if created:
        seed_business_defaults(instance)
