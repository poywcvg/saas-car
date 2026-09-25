from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.customers.models import Customer
from core.access import current_business

from .forms import VehicleForm
from .models import Vehicle


@login_required
def vehicle_add(request, customer_pk):
    business = current_business(request)
    if not business:
        return redirect("businesses:create")

    customer = get_object_or_404(Customer, pk=customer_pk, business=business)

    if request.method == "POST":
        form = VehicleForm(request.POST, business=business)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.customer = customer
            vehicle.save()
            messages.success(request, "خودرو اضافه شد")
            return redirect("customers:detail", pk=customer.pk)
    else:
        form = VehicleForm(business=business)

    return render(
        request,
        "vehicles/add.html",
        {"form": form, "customer": customer},
    )


@login_required
def vehicle_edit(request, pk):
    business = current_business(request)
    if not business:
        return redirect("businesses:create")

    vehicle = get_object_or_404(
        Vehicle.objects.select_related("customer"),
        pk=pk,
        customer__business=business,
    )

    if request.method == "POST":
        form = VehicleForm(request.POST, instance=vehicle, business=business)
        if form.is_valid():
            form.save()
            messages.success(request, "مشخصات خودرو بروزرسانی شد")
            return redirect("vehicles:detail", pk=vehicle.pk)
    else:
        form = VehicleForm(instance=vehicle, business=business)

    return render(
        request,
        "vehicles/edit.html",
        {"form": form, "vehicle": vehicle, "customer": vehicle.customer},
    )


@login_required
def vehicle_detail(request, pk):
    business = current_business(request)
    if not business:
        return redirect("businesses:create")

    vehicle = get_object_or_404(
        Vehicle.objects.select_related("customer"),
        pk=pk,
        customer__business=business,
    )
    changes = vehicle.oil_changes.all()

    return render(
        request,
        "vehicles/detail.html",
        {"vehicle": vehicle, "customer": vehicle.customer, "changes": changes},
    )
