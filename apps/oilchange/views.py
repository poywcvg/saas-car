from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.catalog.models import Product
from apps.vehicles.models import Vehicle
from core.access import current_business

from .forms import OilChangeForm


@login_required
def oilchange_add(request, vehicle_pk):
    business = current_business(request)
    if not business:
        return redirect("businesses:create")

    vehicle = get_object_or_404(
        Vehicle.objects.select_related("customer"),
        pk=vehicle_pk,
        customer__business=business,
    )

    if request.method == "POST":
        form = OilChangeForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.vehicle = vehicle
            record.created_by = request.user
            record.product = Product.objects.filter(slug="oil-change").first()
            record.save()
            vehicle.refresh_service_status()
            messages.success(request, "تعویض روغن ثبت شد؛ موعد بعدی حساب شد.")
            return redirect("customers:detail", pk=vehicle.customer.pk)
    else:
        # پیش‌فرض‌ها: اول از تنظیمات سطحِ خودرو، بعد ادامه از آخرین تعویض
        last = vehicle.latest_oilchange
        initial = {}
        if vehicle.service_interval_km:
            initial["interval_km"] = vehicle.service_interval_km
        if vehicle.service_interval_months:
            initial["interval_months"] = vehicle.service_interval_months
        if vehicle.preferred_oil_id:
            initial["oil_name"] = vehicle.preferred_oil.name
        if last is not None:
            # فاصله‌ها را اگر خودرو تعیین نکرده، از آخرین تعویض بردار
            initial.setdefault("interval_km", last.interval_km)
            initial.setdefault("interval_months", last.interval_months)
            # نام روغنِ آخرین سرویس برای پیوستگی اولویت دارد
            if last.oil_name:
                initial["oil_name"] = last.oil_name
        # کارکرد را با کارکرد تخمینیِ امروز پیش‌پر کن تا اپراتور فقط اصلاح کند
        estimated = vehicle.estimated_current_mileage
        if estimated is not None:
            initial["mileage_km"] = estimated
        form = OilChangeForm(initial=initial)

    return render(
        request,
        "oilchange/add.html",
        {
            "form": form,
            "vehicle": vehicle,
            "customer": vehicle.customer,
            # زمینه برای ماشین‌حساب حرفه‌ای زندهٔ درون صفحه
            "estimated_mileage": vehicle.estimated_current_mileage,
            "daily_km": round(vehicle.daily_km),
            "last_mileage": vehicle.last_mileage_km,
        },
    )
