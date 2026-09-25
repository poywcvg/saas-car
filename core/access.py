"""کمک‌تابع‌های مشترک برای دسترسی به کسب‌وکار کاربر."""

from apps.businesses.models import Business


def user_business(user):
    """اولین کسب‌وکاری که کاربر در آن عضو است را برمی‌گرداند (یا None)."""
    if not user.is_authenticated:
        return None
    return (
        Business.objects.filter(memberships__user=user)
        .distinct()
        .first()
    )


def user_is_member(user, business):
    """آیا کاربر عضوِ این کسب‌وکار است؟"""
    if business is None or not user.is_authenticated:
        return False
    return business.memberships.filter(user=user).exists()


def user_role_in(user, business):
    """نقش کاربر در کسب‌وکار (owner/manager/employee) یا None اگر عضو نیست."""
    if business is None or not getattr(user, "is_authenticated", False):
        return None
    membership = business.memberships.filter(user=user).only("role").first()
    return membership.role if membership else None


def current_business(request):
    """
    کسب‌وکار «فعالِ» این درخواست را برمی‌گرداند.

    - روی ساب‌دامین نماینده (request.is_tenant): همان کسب‌وکارِ میزبان،
      اما فقط اگر کاربر عضوِ آن باشد؛ در غیر این صورت None (پنل ادمین
      نباید داده‌ی مستأجرِ دیگر را نشت دهد).
    - روی میزبان پلتفرم: اولین کسب‌وکارِ خودِ کاربر (رفتار قدیمی).
    """
    if getattr(request, "is_tenant", False) and request.business is not None:
        if user_is_member(request.user, request.business):
            return request.business
        return None
    return user_business(request.user)
