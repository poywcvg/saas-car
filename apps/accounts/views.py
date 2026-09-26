import json

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.businesses.models import Membership
from apps.orders.models import Order
from core.access import current_business, user_role_in
from core.sms import send_sms

from .forms import LoginForm, MemberEditForm, MemberRoleForm, OTPForm, ProfileForm, RegisterForm
from .models import OTP

User = get_user_model()


def _safe_next(request, default="businesses:dashboard"):
    """مقصدِ ?next= فقط اگر داخل همین سایت باشد (جلوگیری از open redirect)."""
    target = request.POST.get("next") or request.GET.get("next") or ""
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return target
    return default


def _auth_context(request, login_form, register_form, active):
    """context مشترک برای قالب یکپارچه‌ی ورود/ثبت‌نام."""
    return {
        "login_form": login_form,
        "register_form": register_form,
        "active": active,  # "login"، "register" یا "otp"
        # فقط مقصدِ امن و داخلی را در فرم‌ها و لینک‌ها نگه می‌داریم
        "next_url": _safe_next(request, default=""),
    }


def login_view(request):
    if request.user.is_authenticated:
        return redirect("businesses:dashboard")

    if request.method == "POST":
        login_form = LoginForm(request, data=request.POST)
        if login_form.is_valid():
            login(request, login_form.get_user())
            messages.success(request, "خوش برگشتی")
            return redirect(_safe_next(request))
        # خطا: همان کارت را با پنل ورود باز نگه دار
        return render(
            request,
            "accounts/auth.html",
            _auth_context(request, login_form, RegisterForm(), "login"),
        )

    return render(
        request,
        "accounts/auth.html",
        _auth_context(request, LoginForm(request), RegisterForm(), "login"),
    )


def otp_login(request):
    """صفحه ورود با کد OTP."""
    if request.user.is_authenticated:
        return redirect("businesses:dashboard")

    return render(
        request,
        "accounts/auth.html",
        _auth_context(request, LoginForm(request), RegisterForm(), "otp"),
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("businesses:dashboard")

    if request.method == "POST":
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            user = register_form.save()
            login(request, user)
            messages.success(request, "خوش اومدی! حالا کسب‌وکارت رو بساز.")
            return redirect("businesses:create")
        # خطا: همان کارت را با پنل ثبت‌نام باز نگه دار
        return render(
            request,
            "accounts/auth.html",
            _auth_context(request, LoginForm(request), register_form, "register"),
        )

    return render(
        request,
        "accounts/auth.html",
        _auth_context(request, LoginForm(request), RegisterForm(), "register"),
    )


@require_POST
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "با موفقیت خارج شدی.")
    # ریشه‌ی همین میزبان: خانه‌ی پلتفرم یا ویترینِ نماینده
    return redirect("/")


@login_required
def profile(request):
    memberships = Membership.objects.filter(user=request.user).select_related("business")
    orders = Order.objects.filter(user=request.user).select_related("business", "product")[:10]

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "پروفایل بروزرسانی شد.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "memberships": memberships,
            "orders": orders,
        },
    )


def _team_permission(request, business, *, owner_only=False):
    """دسترسی مدیریت تیم: مالک و مدیر برای ویرایش، فقط مالک برای سطح دسترسی.

    برمی‌گرداند (نقش، پاسخ): اگر دسترسی نباشد، پاسخ ریدایرکت است.
    """
    allowed = (
        (Membership.Role.OWNER,)
        if owner_only
        else (Membership.Role.OWNER, Membership.Role.MANAGER)
    )
    role = user_role_in(request.user, business)
    if role not in allowed:
        messages.error(request, "برای مدیریت اعضای تیم دسترسی ندارید.")
        return None, redirect("businesses:dashboard")
    return role, None


def _other_owners_exist(business, exclude_user_id):
    """آیا به‌جز این کاربر، مالک دیگری در تیم هست؟ (محافظ آخرین مالک)"""
    return (
        Membership.objects.filter(business=business, role=Membership.Role.OWNER)
        .exclude(user_id=exclude_user_id)
        .exists()
    )


@login_required
def team_list(request):
    """فهرست اعضای تیم کسب‌وکار فعال — ویژه‌ی مالک و مدیر."""
    business = current_business(request)
    if not business:
        return redirect("businesses:create")
    role, denied = _team_permission(request, business)
    if denied:
        return denied

    members = (
        Membership.objects.filter(business=business)
        .select_related("user")
        .order_by("-role", "user__username")
    )
    return render(
        request,
        "accounts/team_list.html",
        {"business": business, "members": members, "my_role": role},
    )


@login_required
def team_member_edit(request, pk):
    """ویرایش مشخصات یک عضو تیم.

    مالک و مدیر: نام، موبایل، ایمیل. فقط مالک (و نه برای خودش):
    نقش، فعال/غیرفعال بودن و حذف از تیم.
    """
    business = current_business(request)
    if not business:
        return redirect("businesses:create")
    role, denied = _team_permission(request, business)
    if denied:
        return denied

    member = get_object_or_404(User, pk=pk)
    membership = get_object_or_404(Membership, user=member, business=business)
    is_self = member.pk == request.user.pk
    can_manage_access = role == Membership.Role.OWNER and not is_self

    if request.method == "POST":
        uform = MemberEditForm(request.POST, instance=member)
        rform = (
            MemberRoleForm(request.POST, instance=membership)
            if can_manage_access
            else None
        )
        new_active = (
            "is_active" in request.POST if can_manage_access else member.is_active
        )
        valid = uform.is_valid() and (rform is None or rform.is_valid())
        # آخرین مالک نباید تنزل نقش بگیرد یا غیرفعال شود
        if valid and can_manage_access and membership.role == Membership.Role.OWNER:
            new_role = rform.cleaned_data["role"]
            if (new_role != Membership.Role.OWNER or not new_active) and not (
                _other_owners_exist(business, member.pk)
            ):
                valid = False
                messages.error(request, "حداقل یک مالک باید در تیم بماند.")
        if valid:
            with transaction.atomic():
                member.is_active = new_active
                uform.save()
                if rform is not None:
                    rform.save()
            display = member.get_full_name() or member.username
            messages.success(request, f"مشخصات «{display}» بروزرسانی شد.")
            return redirect("accounts:team")
        # بازتاب انتخابِ فعال‌بودن در رندر مجدد فرم خطادار
        member.is_active = new_active
    else:
        uform = MemberEditForm(instance=member)
        rform = (
            MemberRoleForm(instance=membership) if can_manage_access else None
        )

    return render(
        request,
        "accounts/team_edit.html",
        {
            "business": business,
            "member": member,
            "membership": membership,
            "uform": uform,
            "rform": rform,
            "is_self": is_self,
            "can_manage_access": can_manage_access,
        },
    )


@login_required
@require_POST
def team_member_remove(request, pk):
    """حذف عضو از تیم (نه حذف حساب کاربری) — فقط مالک."""
    business = current_business(request)
    if not business:
        return redirect("businesses:create")
    _, denied = _team_permission(request, business, owner_only=True)
    if denied:
        return denied

    member = get_object_or_404(User, pk=pk)
    membership = get_object_or_404(Membership, user=member, business=business)
    if member.pk == request.user.pk:
        messages.error(request, "نمی‌توانید خودتان را از تیم حذف کنید.")
        return redirect("accounts:team_edit", pk=pk)
    if membership.role == Membership.Role.OWNER and not _other_owners_exist(
        business, member.pk
    ):
        messages.error(request, "آخرین مالک را نمی‌توان از تیم حذف کرد.")
        return redirect("accounts:team_edit", pk=pk)

    display = member.get_full_name() or member.username
    membership.delete()
    messages.success(request, f"«{display}» از تیم حذف شد.")
    return redirect("accounts:team")


def send_otp(request):
    """ارسال کد OTP به شماره موبایل."""
    if request.method != "POST":
        return redirect("accounts:login")

    phone = request.POST.get("phone", "").strip()

    if not phone:
        messages.error(request, "شماره موبایل را وارد کنید.")
        return redirect("accounts:login")

    otp = OTP.generate(phone)
    send_sms(phone, f"کد تایید چرخیار: {otp.code}\nاین کد تا ۵ دقیقه معتبر است.")

    request.session["otp_phone"] = phone
    request.session["otp_sent"] = True

    messages.success(request, f"کد تایید به {phone} ارسال شد.")
    return redirect("accounts:verify_otp")


def verify_otp(request):
    """تایید کد OTP و ورود/ثبت‌نام."""
    if not request.session.get("otp_sent"):
        return redirect("accounts:login")

    phone = request.session.get("otp_phone", "")

    if request.method == "POST":
        form = OTPForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            otp = OTP.objects.filter(
                phone=phone, code=code, is_used=False
            ).order_by("-created_at").first()

            if otp and otp.is_valid():
                otp.mark_used()

                user, created = User.objects.get_or_create(
                    phone=phone,
                    defaults={"username": phone, "first_name": phone},
                )

                del request.session["otp_phone"]
                del request.session["otp_sent"]

                login(request, user)
                messages.success(request, "خوش آمدید!")

                if created:
                    messages.info(request, "حساب جدید ساخته شد. حالا پروفایل خود را تکمیل کنید.")
                    return redirect("accounts:profile")
                return redirect(_safe_next(request))
            else:
                messages.error(request, "کد تایید نادرست یا منقضی شده است.")
    else:
        form = OTPForm()

    return render(
        request,
        "accounts/verify_otp.html",
        {"form": form, "phone": phone},
    )


@require_POST
def resend_otp(request):
    """ارسال مجدد کد OTP."""
    phone = request.session.get("otp_phone", "")
    if not phone:
        return redirect("accounts:login")

    otp = OTP.generate(phone)
    send_sms(phone, f"کد تایید چرخیار: {otp.code}\nاین کد تا ۵ دقیقه معتبر است.")

    messages.success(request, f"کد جدید به {phone} ارسال شد.")
    return redirect("accounts:verify_otp")
