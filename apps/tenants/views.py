"""ویوهای سایتِ عمومیِ هر نماینده (ویترین + پورتال مشتری).

این ویوها فقط در بافتِ مستأجر (request.is_tenant) و از طریق
config.urls_tenant فراخوانی می‌شوند. همه‌چیز به request.business محدود است.
"""
from django.http import Http404
from django.shortcuts import render

from apps.vehicles.models import Vehicle
from core.normalize import normalize_phone, normalize_plate


def _tenant(request):
    business = getattr(request, "business", None)
    if business is None:
        raise Http404()
    return business


def storefront(request):
    """ویترین/لندینگِ نماینده با برندِ خودش."""
    business = _tenant(request)
    return render(
        request,
        "tenants/storefront.html",
        {"business": business},
    )


def lookup(request):
    """
    پورتال مشتری: جست‌وجو با شماره موبایل یا پلاک — بدون ثبت‌نام.
    نتیجه: خودروها و وضعیت سرویسِ همان مشتری، محدود به این کسب‌وکار.
    """
    business = _tenant(request)

    raw = (request.GET.get("q") or "").strip()
    submitted = bool(raw)
    customers = []
    vehicles = []

    if submitted:
        phone = normalize_phone(raw)
        plate = normalize_plate(raw)

        cust_qs = business.customers.all()
        matched_customers = set()

        # ۱) تطبیق با شماره موبایل (اگر ورودی شبیه شماره بود)
        if len(phone) >= 7:
            for c in cust_qs:
                if normalize_phone(c.phone) == phone:
                    matched_customers.add(c.pk)

        # ۲) تطبیق با پلاک روی خودروها
        veh_qs = (
            Vehicle.objects
            .filter(customer__business=business)
            .select_related("customer")
        )
        if plate and len(plate) >= 4:
            for v in veh_qs:
                if plate in normalize_plate(v.plate):
                    matched_customers.add(v.customer_id)

        if matched_customers:
            customers = list(
                cust_qs.filter(pk__in=matched_customers).prefetch_related("vehicles")
            )
            for c in customers:
                for v in c.vehicles.all():
                    vehicles.append(v)

    return render(
        request,
        "tenants/lookup.html",
        {
            "business": business,
            "query": raw,
            "submitted": submitted,
            "customers": customers,
            "vehicles": vehicles,
            "found": bool(customers),
        },
    )
