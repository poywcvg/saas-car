import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.oilchange.models import OilChange
from apps.vehicles.models import Vehicle
from core import service_status
from core.access import current_business, user_business
from core.sms import build_reminder_text

from .forms import BusinessForm
from .models import Membership


@login_required
def create_business(request):
    # اگر کاربر از قبل کسب‌وکاری دارد، به داشبورد برود
    existing = user_business(request.user)
    if existing:
        return redirect("businesses:dashboard")

    if request.method == "POST":
        form = BusinessForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                business = form.save(commit=False)
                business.owner = request.user
                business.save()

                Membership.objects.create(
                    user=request.user,
                    business=business,
                    role=Membership.Role.OWNER,
                )

            messages.success(request, "کسب‌وکارت ساخته شد!")
            return redirect("businesses:dashboard")
    else:
        form = BusinessForm()

    return render(request, "businesses/create.html", {"form": form})


@login_required
def dashboard(request):
    business = current_business(request)
    if not business:
        return redirect("businesses:create")

    today = datetime.date.today()
    soon = today + datetime.timedelta(days=service_status.DUE_SOON_DAYS)
    month_start = today.replace(day=1)

    vehicles = Vehicle.objects.filter(customer__business=business)
    services = OilChange.objects.filter(vehicle__customer__business=business)

    stats = {
        "customers": business.customers.count(),
        "vehicles": vehicles.count(),
        "due_soon": vehicles.filter(
            next_due_date__gte=today, next_due_date__lte=soon
        ).count(),
        "overdue": vehicles.filter(next_due_date__lt=today).count(),
        "this_month": services.filter(service_date__gte=month_start).count(),
        "total_services": services.count(),
    }

    # خودروهایی که نیاز به توجه دارند (گذشته یا نزدیک موعد)، مرتب بر اساس فوریت
    attention = list(
        vehicles.filter(next_due_date__lte=soon)
        .select_related("customer")
        .order_by("next_due_date")[:8]
    )

    recent_customers = business.customers.prefetch_related("vehicles")[:6]

    # آخرین فعالیت‌ها: تعویض روغن‌های اخیر
    recent_services = list(
        services.select_related("vehicle", "vehicle__customer").order_by("-created_at")[:6]
    )

    context = {
        "business": business,
        "stats": stats,
        "attention": attention,
        "recent_customers": recent_customers,
        "recent_services": recent_services,
    }
    return render(request, "businesses/dashboard.html", context)


@login_required
def reminders(request):
    """فهرست خودروهای گذشته از موعد و نزدیک موعد، همراه با دکمه‌ی پیامک سریع."""
    business = current_business(request)
    if not business:
        return redirect("businesses:create")

    today = datetime.date.today()
    soon = today + datetime.timedelta(days=service_status.DUE_SOON_DAYS)

    base = (
        Vehicle.objects.filter(customer__business=business, next_due_date__isnull=False)
        .select_related("customer")
        .order_by("next_due_date")
    )

    def build_items(queryset):
        items = []
        for vehicle in queryset:
            customer = vehicle.customer
            public_path = reverse(
                "public_customer", kwargs={"token": customer.public_token}
            )
            public_url = request.build_absolute_uri(public_path)
            items.append(
                {
                    "vehicle": vehicle,
                    "customer": customer,
                    "days": vehicle.days_until_due,
                    "sms_body": build_reminder_text(customer, public_url, business.name),
                }
            )
        return items

    overdue = build_items(base.filter(next_due_date__lt=today))
    due_soon = build_items(base.filter(next_due_date__gte=today, next_due_date__lte=soon))

    context = {
        "business": business,
        "overdue": overdue,
        "due_soon": due_soon,
        "total": len(overdue) + len(due_soon),
    }
    return render(request, "businesses/reminders.html", context)
