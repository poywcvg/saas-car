"""مدیریت لیست‌های پایه‌ی خودرو توسط صاحب کسب‌وکار (برند/مدل/رنگ/روغن/سوخت)."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from apps.catalog.models import Product
from core import seo
from core.access import current_business

from .models import VehicleBrand, VehicleModel, VehicleOption

# انواع گزینه‌ای که در این صفحه مدیریت می‌شوند
OPTION_KINDS = [
    ("color", "رنگ‌ها"),
    ("oil", "نوع روغن"),
    ("fuel", "نوع سوخت"),
]


def _add_brand(business, request):
    name = (request.POST.get("name") or "").strip()
    if not name:
        messages.error(request, "نام برند را وارد کنید.")
        return
    try:
        VehicleBrand.objects.create(business=business, name=name)
        messages.success(request, f"برند «{name}» اضافه شد.")
    except IntegrityError:
        messages.error(request, "این برند از قبل وجود دارد.")


def _add_model(business, request):
    name = (request.POST.get("name") or "").strip()
    brand = get_object_or_404(
        VehicleBrand, pk=request.POST.get("brand"), business=business
    )
    if not name:
        messages.error(request, "نام مدل را وارد کنید.")
        return
    try:
        VehicleModel.objects.create(brand=brand, name=name)
        messages.success(request, f"مدل «{name}» به «{brand.name}» اضافه شد.")
    except IntegrityError:
        messages.error(request, "این مدل از قبل برای این برند وجود دارد.")


def _add_option(business, request):
    name = (request.POST.get("name") or "").strip()
    kind = request.POST.get("kind")
    if kind not in dict(VehicleOption.Kind.choices):
        messages.error(request, "نوع گزینه نامعتبر است.")
        return
    if not name:
        messages.error(request, "عنوان را وارد کنید.")
        return
    try:
        VehicleOption.objects.create(business=business, kind=kind, name=name)
        messages.success(request, f"«{name}» اضافه شد.")
    except IntegrityError:
        messages.error(request, "این گزینه از قبل وجود دارد.")


def _unique_product_slug(business, title):
    """اسلاگِ یکتا در محدوده‌ی همین کسب‌وکار می‌سازد."""
    base = slugify(title, allow_unicode=True) or "service"
    slug = base
    i = 2
    while Product.objects.filter(business=business, slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug


def _add_product(business, request):
    title = (request.POST.get("name") or "").strip()
    tagline = (request.POST.get("tagline") or "").strip()
    if not title:
        messages.error(request, "نام خدمت را وارد کنید.")
        return
    Product.objects.create(
        business=business,
        title=title,
        tagline=tagline,
        slug=_unique_product_slug(business, title),
        is_available=True,
    )
    messages.success(request, f"خدمت «{title}» اضافه شد.")


def _update_business(business, request):
    """اطلاعات عمومی کسب‌وکار — همان چیزی که گوگل و مشتری می‌بینند."""
    business.city = (request.POST.get("city") or "").strip()
    business.tagline = (request.POST.get("tagline") or "").strip()[:160]
    business.phone = (request.POST.get("phone") or "").strip()
    business.address = (request.POST.get("address") or "").strip()
    business.is_listed = request.POST.get("is_listed") == "1"
    business.save(
        update_fields=["city", "tagline", "phone", "address", "is_listed"]
    )
    messages.success(request, "اطلاعات کسب‌وکار ذخیره شد.")


def _toggle(business, request):
    kind = request.POST.get("obj_type")
    pk = request.POST.get("obj_id")
    obj = _get_owned(business, kind, pk)
    if obj is None:
        return
    # محصولات فیلدشان is_available است؛ بقیه is_active
    field = "is_available" if kind == "product" else "is_active"
    setattr(obj, field, not getattr(obj, field))
    obj.save(update_fields=[field])


def _delete(business, request):
    kind = request.POST.get("obj_type")
    pk = request.POST.get("obj_id")
    obj = _get_owned(business, kind, pk)
    if obj is None:
        return
    label = str(obj)
    obj.delete()
    messages.success(request, f"«{label}» حذف شد.")


def _get_owned(business, kind, pk):
    """یک آبجکتِ متعلق به همین کسب‌وکار را برمی‌گرداند یا None."""
    if not pk:
        return None
    if kind == "brand":
        return VehicleBrand.objects.filter(business=business, pk=pk).first()
    if kind == "model":
        return VehicleModel.objects.filter(brand__business=business, pk=pk).first()
    if kind == "option":
        return VehicleOption.objects.filter(business=business, pk=pk).first()
    if kind == "product":
        # فقط خدمات سفارشیِ همین کسب‌وکار (نه محصولات سراسری)
        return Product.objects.filter(business=business, pk=pk).first()
    return None


ACTIONS = {
    "update_business": _update_business,
    "add_brand": _add_brand,
    "add_model": _add_model,
    "add_option": _add_option,
    "add_product": _add_product,
    "toggle": _toggle,
    "delete": _delete,
}


@login_required
def garage_settings(request):
    business = current_business(request)
    if not business:
        return redirect("businesses:create")

    if request.method == "POST":
        handler = ACTIONS.get(request.POST.get("action"))
        if handler:
            handler(business, request)
        return redirect("garage:settings")

    brands = (
        VehicleBrand.objects.filter(business=business)
        .prefetch_related("models")
    )
    options_by_kind = [
        {
            "kind": kind,
            "label": label,
            "items": VehicleOption.objects.filter(business=business, kind=kind),
        }
        for kind, label in OPTION_KINDS
    ]
    # خدمات سفارشیِ همین کسب‌وکار (قابل ویرایش) و خدمات سراسری (فقط نمایش)
    custom_products = Product.objects.filter(business=business).order_by(
        "-is_available", "sort_order", "title"
    )
    platform_products = Product.objects.filter(business__isnull=True).order_by(
        "sort_order", "title"
    )

    return render(
        request,
        "garage/settings.html",
        {
            "business": business,
            "brands": brands,
            "options_by_kind": options_by_kind,
            "custom_products": custom_products,
            "platform_products": platform_products,
            # اگر شهرِ کسب‌وکار جزو شهرهای هدفِ سئو باشد، لینک صفحه‌ی شهر
            "city_page_path": (
                seo.city_page_path(business.city)
                if business.city in settings.SEO_CITIES
                else ""
            ),
        },
    )
