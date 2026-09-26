from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from apps.oilchange.models import OilChange
from apps.vehicles.models import Vehicle
from apps.vehicles.selectors import due_vehicles
from core.access import current_business, user_business
from core.normalize import digits_only, normalize_phone, to_ascii_digits
from core.sms import build_reminder_text

from .forms import BusinessForm
from .models import Business, Membership
from django.utils import timezone


def _reminder_item(request, business, vehicle):
    """یک ردیفِ یادآوری: خودرو + مشتری + روزهای مانده + متن آماده‌ی پیامک."""
    customer = vehicle.customer
    public_path = reverse("public_customer", kwargs={"token": customer.public_token})
    public_url = request.build_absolute_uri(public_path)
    return {
        "vehicle": vehicle,
        "customer": customer,
        "days": vehicle.days_until_due,
        "sms_body": build_reminder_text(customer, public_url, business.name),
    }


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

    today = timezone.localdate()
    month_start = today.replace(day=1)

    vehicles = Vehicle.objects.filter(customer__business=business)
    services = OilChange.objects.filter(vehicle__customer__business=business)

    # موعد مؤثر (تاریخی یا کیلومتری، هر کدام زودتر) — همان منطقِ یادآوری‌ها
    overdue, due_soon = due_vehicles(business)
    serviced = vehicles.filter(last_service_date__isnull=False).count()

    stats = {
        "customers": business.customers.count(),
        "vehicles": vehicles.count(),
        "due_soon": len(due_soon),
        "overdue": len(overdue),
        "ok": max(serviced - len(overdue) - len(due_soon), 0),
        "this_month": services.filter(service_date__gte=month_start).count(),
        "today": services.filter(service_date=today).count(),
        "total_services": services.count(),
    }

    # خودروهایی که نیاز به توجه دارند (گذشته یا نزدیک موعد)، مرتب بر اساس فوریت
    attention = [
        _reminder_item(request, business, v) for v in (overdue + due_soon)[:6]
    ]

    # آخرین فعالیت‌ها: تعویض روغن‌های اخیر
    recent_services = list(
        services.select_related("vehicle", "vehicle__customer").order_by("-created_at")[:6]
    )

    context = {
        "business": business,
        "stats": stats,
        "today": today,
        "attention": attention,
        "attention_more": max(len(overdue) + len(due_soon) - len(attention), 0),
        "recent_services": recent_services,
    }
    return render(request, "businesses/dashboard.html", context)


@login_required
def reminders(request):
    """فهرست خودروهای گذشته از موعد و نزدیک موعد، همراه با دکمه‌ی پیامک سریع."""
    business = current_business(request)
    if not business:
        return redirect("businesses:create")

    overdue_v, due_soon_v = due_vehicles(business)
    overdue = [_reminder_item(request, business, v) for v in overdue_v]
    due_soon = [_reminder_item(request, business, v) for v in due_soon_v]

    context = {
        "business": business,
        "overdue": overdue,
        "due_soon": due_soon,
        "total": len(overdue) + len(due_soon),
    }
    return render(request, "businesses/reminders.html", context)


@login_required
def quick_service(request):
    """ثبت سریع تعویض روغن: جست‌وجو با موبایل، پلاک یا اسم → یک دکمه.

    ساده‌ترین مسیر برای کاربرِ پرمشغله یا کم‌سواد: شماره را می‌زند، ماشین را
    می‌بیند و «ثبت تعویض روغن» را لمس می‌کند.
    """
    business = current_business(request)
    if not business:
        return redirect("businesses:create")

    q = to_ascii_digits(request.GET.get("q", "")).strip()
    digits = digits_only(q)
    vehicles = []
    customers_without_vehicle = []
    if q:
        cond = Q(customer__full_name__icontains=q) | Q(plate__icontains=q)
        cust_cond = Q(full_name__icontains=q)
        if len(digits) >= 3:
            phone_part = normalize_phone(digits) if len(digits) >= 10 else digits
            cond |= Q(customer__phone__contains=phone_part) | Q(plate__contains=digits)
            cust_cond |= Q(phone__contains=phone_part)
        vehicles = list(
            Vehicle.objects.filter(customer__business=business)
            .filter(cond)
            .select_related("customer")
            .distinct()[:20]
        )
        customers_without_vehicle = list(
            business.customers.filter(cust_cond, vehicles__isnull=True)[:10]
        )

    return render(
        request,
        "businesses/quick.html",
        {
            "business": business,
            "q": q,
            "vehicles": vehicles,
            "customers_without_vehicle": customers_without_vehicle,
            # اگر عبارتِ جست‌وجو شماره‌ی موبایل است، «مشتری جدید» با همین شماره پر شود
            "prefill_phone": normalize_phone(digits) if len(digits) >= 10 else "",
        },
    )


def _location_business(request):
    """کسب‌وکارِ هدف برای ثبت لوکیشن: ?b=<id> از مغازه‌های خودِ کاربر، وگرنه مغازه‌ی فعلی."""
    raw = request.GET.get("b") or request.POST.get("b")
    if raw and raw.isdigit():
        return (
            Business.objects.filter(pk=int(raw), memberships__user=request.user)
            .distinct()
            .first()
        )
    return current_business(request)


def can_edit_location(user, business):
    """مالک/مدیر، یا هر کسی که برای این مغازه محصولی سفارش داده."""
    if business is None:
        return False
    role = business.memberships.filter(user=user).values_list("role", flat=True).first()
    if role in (Membership.Role.OWNER, Membership.Role.MANAGER):
        return True
    return business.orders.filter(user=user).exclude(status="cancelled").exists()


def _parse_coord(raw, limit):
    try:
        value = Decimal(to_ascii_digits((raw or "").strip()))
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite() or abs(value) > limit:
        return None
    return value.quantize(Decimal("0.000001"))


@login_required
def business_location(request):
    """ثبت لوکیشن مغازه روی نقشه — فقط برای مغازه‌ای که محصولی خریده."""
    business = _location_business(request)
    if business is None:
        return redirect("businesses:create")

    next_url = request.GET.get("next") or request.POST.get("next") or ""
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = ""

    purchased = business.has_purchase
    allowed = purchased and can_edit_location(request.user, business)

    if request.method == "POST" and allowed:
        if request.POST.get("action") == "clear":
            business.latitude = business.longitude = None
            business.save(update_fields=["latitude", "longitude", "updated_at"])
            messages.success(request, "لوکیشن مغازه پاک شد.")
            return redirect(f"{reverse('businesses:location')}?b={business.pk}")

        lat = _parse_coord(request.POST.get("lat"), 90)
        lng = _parse_coord(request.POST.get("lng"), 180)
        if lat is None or lng is None:
            messages.error(request, "جای مغازه معلوم نشد. نقشه را جابه‌جا کن و دوباره بزن.")
        else:
            business.latitude, business.longitude = lat, lng
            business.save(update_fields=["latitude", "longitude", "updated_at"])
            messages.success(request, "لوکیشن مغازه ثبت شد. حالا مشتری‌ها با یک دکمه پیدات می‌کنند.")
            return redirect(next_url or f"{reverse('businesses:location')}?b={business.pk}")

    # نقطه‌ی شروع نقشه: لوکیشن ثبت‌شده، وگرنه مرکز شهر، وگرنه شهر اصلی
    if business.has_location:
        start = (float(business.latitude), float(business.longitude), 17)
    else:
        city_geo = settings.SEO_CITY_GEO.get(business.city) or settings.SEO_CITY_GEO.get(
            settings.SEO_PRIMARY_CITY
        )
        start = (city_geo[0], city_geo[1], 13) if city_geo else (32.4, 53.7, 5)

    return render(
        request,
        "businesses/location.html",
        {
            "business": business,
            "purchased": purchased,
            "allowed": allowed,
            "start": start,
            "next_url": next_url,
        },
    )
