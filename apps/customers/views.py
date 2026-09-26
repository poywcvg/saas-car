from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.vehicles.forms import VehicleForm
from core.access import current_business
from core.normalize import to_ascii_digits
from core.sms import build_reminder_text

from .forms import CustomerForm
from .models import Customer


@login_required
def customer_list(request):
    business = current_business(request)
    if not business:
        return redirect("businesses:create")

    # ارقام فارسی را لاتین کن تا «۰۹۱۲» هم پیدا شود؛ پلاک هم جست‌وجو می‌شود
    q = to_ascii_digits(request.GET.get("q", "")).strip()
    customers = business.customers.prefetch_related("vehicles")
    if q:
        customers = customers.filter(
            Q(full_name__icontains=q)
            | Q(phone__icontains=q)
            | Q(vehicles__plate__icontains=q)
        ).distinct()

    return render(
        request,
        "customers/list.html",
        {"business": business, "customers": customers, "q": q},
    )


@login_required
def customer_add(request):
    business = current_business(request)
    if not business:
        return redirect("businesses:create")

    if request.method == "POST":
        cform = CustomerForm(request.POST, business=business)
        vform = VehicleForm(request.POST, business=business)
        # خودرو اختیاری است: فقط اگر کاربر واقعاً چیزی در بخش خودرو وارد
        # کرده، فرم خودرو اعتبارسنجی و ذخیره می‌شود؛ وگرنه فقط مشتری ثبت
        # می‌شود. (باگ قبلی: فرم خالی خودرو همیشه is_valid را False می‌کرد و
        # مشتری حتی با اسم و موبایلِ درست هم ثبت نمی‌شد. از has_changed استفاده
        # نشد چون initial پیش‌فرض مدل (مثل کیلومتر ۰) آن را همیشه True می‌کند.)
        has_vehicle = any(
            (request.POST.get(field) or "").strip()
            for field in VehicleForm.Meta.fields
        )
        if cform.is_valid() and (not has_vehicle or vform.is_valid()):
            with transaction.atomic():
                customer = cform.save(commit=False)
                customer.business = business
                customer.save()

                if has_vehicle:
                    vehicle = vform.save(commit=False)
                    vehicle.customer = customer
                    vehicle.save()

            if has_vehicle:
                messages.success(
                    request, f"مشتری «{customer.full_name}» و خودرو با موفقیت ثبت شد"
                )
            else:
                messages.success(
                    request, f"مشتری «{customer.full_name}» با موفقیت ثبت شد"
                )
            # دکمه‌ی «ثبت و تعویض روغن»: یکراست برو سراغ فرم تعویض
            if request.POST.get("then") == "oil":
                if has_vehicle:
                    return redirect("oilchange:add", vehicle_pk=vehicle.pk)
                messages.info(request, "حالا ماشینش را ثبت کن.")
                return redirect("vehicles:add", customer_pk=customer.pk)
            return redirect("customers:detail", pk=customer.pk)
    else:
        # از صفحه‌ی «ثبت سریع»: شماره‌ی جست‌وجوشده از قبل پر شود
        cform = CustomerForm(
            business=business,
            initial={"phone": request.GET.get("phone", "")[:20]},
        )
        vform = VehicleForm(business=business)

    return render(
        request,
        "customers/add.html",
        {
            "cform": cform,
            "vform": vform,
            "duplicate": getattr(cform, "duplicate", None),
        },
    )


@login_required
def customer_detail(request, pk):
    business = current_business(request)
    if not business:
        return redirect("businesses:create")

    customer = get_object_or_404(
        Customer.objects.prefetch_related("vehicles"),
        pk=pk,
        business=business,
    )

    public_path = reverse("public_customer", kwargs={"token": customer.public_token})
    public_url = request.build_absolute_uri(public_path)
    sms_body = build_reminder_text(customer, public_url, business.name)

    return render(
        request,
        "customers/detail.html",
        {
            "customer": customer,
            "business": business,
            "public_url": public_url,
            "sms_body": sms_body,
        },
    )


@login_required
def customer_edit(request, pk):
    business = current_business(request)
    if not business:
        return redirect("businesses:create")

    customer = get_object_or_404(Customer, pk=pk, business=business)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer, business=business)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"مشخصات «{customer.full_name}» بروزرسانی شد"
            )
            return redirect("customers:detail", pk=customer.pk)
    else:
        form = CustomerForm(instance=customer, business=business)

    return render(
        request,
        "customers/edit.html",
        {"form": form, "customer": customer},
    )


def public_customer(request, token):
    """صفحه‌ی عمومی مشتری — از طریق لینک پیامکی، بدون نیاز به ورود."""
    customer = get_object_or_404(
        Customer.objects.select_related("business").prefetch_related("vehicles"),
        public_token=token,
    )
    return render(request, "customers/public.html", {"customer": customer})
