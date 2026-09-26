from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.businesses.models import Membership
from apps.businesses.views import can_edit_location
from apps.catalog.models import Product

from .forms import OrderForm
from .models import Order


@login_required
def order_create(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_available=True)

    memberships = Membership.objects.filter(user=request.user).select_related("business")
    if not memberships.exists():
        messages.warning(request, "اول یک کسب‌وکار بسازید.")
        return redirect("businesses:create")

    if request.method == "POST":
        form = OrderForm(user=request.user, product=product, data=request.POST)
        if form.is_valid():
            order = form.save()
            messages.success(request, "سفارش ثبت شد.")
            # صفحه‌ی سفارش، پیشنهادِ (بی‌مزاحمتِ) ثبت لوکیشن مغازه را نشان می‌دهد
            return redirect("orders:detail", pk=order.pk)
    else:
        form = OrderForm(user=request.user, product=product)

    return render(
        request,
        "orders/create.html",
        {"form": form, "product": product},
    )


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).select_related(
        "business", "product"
    )
    return render(request, "orders/list.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("business", "product", "user"),
        pk=pk,
        user=request.user,
    )
    business = order.business
    return render(
        request,
        "orders/detail.html",
        {
            "order": order,
            "can_set_location": order.status != Order.Status.CANCELLED
            and can_edit_location(request.user, business),
        },
    )
