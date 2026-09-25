from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render

from core.access import current_business

from .models import Product


@login_required
def products(request):
    """صفحه‌ی «محصولات من» داخل پنل: محصولات فعال و به‌زودی."""
    business = current_business(request)
    if not business:
        return redirect("businesses:create")

    # محصولات سراسری + خدمات سفارشیِ همین کسب‌وکار
    all_products = list(
        Product.objects.filter(Q(business__isnull=True) | Q(business=business))
    )
    available = [p for p in all_products if p.is_available]
    coming_soon = [p for p in all_products if not p.is_available]

    return render(
        request,
        "catalog/products.html",
        {
            "business": business,
            "available": available,
            "coming_soon": coming_soon,
        },
    )
