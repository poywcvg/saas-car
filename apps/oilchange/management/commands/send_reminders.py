"""ارسال پیامک یادآوری برای خودروهای نزدیک موعد یا گذشته از موعد.

استفاده:
    python manage.py send_reminders            # ارسال (چاپ در کنسول)
    python manage.py send_reminders --days 7   # فقط تا ۷ روز آینده
    python manage.py send_reminders --dry-run  # فقط نمایش، بدون ارسال
"""

import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from apps.customers.models import Customer
from apps.vehicles.models import Vehicle
from core import service_status
from core.sms import build_reminder_text, send_sms


class Command(BaseCommand):
    help = "ارسال پیامک یادآوری تعویض روغن به مشتریانِ نزدیک موعد یا گذشته."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=service_status.DUE_SOON_DAYS,
            help="چند روز آینده «نزدیک موعد» حساب شود (پیش‌فرض: ۱۴).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="فقط نمایش بده، پیامکی ارسال (چاپ) نکن.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        today = datetime.date.today()
        cutoff = today + datetime.timedelta(days=days)

        due_vehicles = (
            Vehicle.objects.filter(next_due_date__isnull=False, next_due_date__lte=cutoff)
            .select_related("customer", "customer__business")
        )

        # مشتریان دارای خودروی نیازمند یادآوری (بدون تکرار)
        customer_ids = {v.customer_id for v in due_vehicles}
        if not customer_ids:
            self.stdout.write(self.style.SUCCESS("موردی برای یادآوری نیست."))
            return

        customers = (
            Customer.objects.filter(id__in=customer_ids)
            .select_related("business")
            .prefetch_related("vehicles")
        )

        sent = 0
        for customer in customers:
            path = reverse("public_customer", kwargs={"token": customer.public_token})
            public_url = f"{settings.SITE_BASE_URL.rstrip('/')}{path}"
            text = build_reminder_text(customer, public_url, customer.business.name)

            if dry_run:
                self.stdout.write(
                    f"[آزمایشی] به {customer.full_name} ({customer.phone})"
                )
            else:
                send_sms(customer.phone, text)
                sent += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"حالت آزمایشی: {len(customer_ids)} مشتری واجد شرایط بودند."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"{sent} پیامک یادآوری ارسال شد.")
            )
