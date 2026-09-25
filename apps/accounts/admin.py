from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import models

from apps.businesses.models import Membership

from .models import User


class MembershipInline(admin.TabularInline):
    """عضویت‌های کاربر در کسب‌وکارها + نقش — مستقیم از صفحه‌ی کاربر."""

    model = Membership
    extra = 0
    autocomplete_fields = ("business",)
    verbose_name = "عضویت در کسب‌وکار"
    verbose_name_plural = "عضویت‌ها در کسب‌وکارها"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "full_name_display",
        "phone",
        "email",
        "businesses_count",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_display_links = ("username", "full_name_display")
    list_editable = ("is_active",)
    list_filter = ("is_staff", "is_active", "groups", "date_joined")
    date_hierarchy = "date_joined"
    ordering = ("-date_joined",)
    search_fields = ("username", "first_name", "last_name", "phone", "email")
    readonly_fields = ("last_login", "date_joined")
    inlines = (MembershipInline,)
    actions = ("activate_users", "deactivate_users")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("مشخصات فردی", {"fields": ("first_name", "last_name", "email", "phone")}),
        (
            "دسترسی‌ها",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("تاریخ‌های مهم", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
        (
            "مشخصات فردی",
            {"fields": ("first_name", "last_name", "email", "phone")},
        ),
        ("دسترسی‌ها", {"fields": ("is_active", "is_staff")}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(_biz_count=models.Count("memberships", distinct=True))
        )

    @admin.display(description="نام کامل", ordering="first_name")
    def full_name_display(self, obj):
        return obj.get_full_name() or "—"

    @admin.display(description="کسب‌وکارها", ordering="_biz_count")
    def businesses_count(self, obj):
        return obj._biz_count

    @admin.action(description="فعال‌سازی کاربران انتخاب‌شده")
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} کاربر فعال شد.")

    @admin.action(description="غیرفعال‌سازی کاربران انتخاب‌شده")
    def deactivate_users(self, request, queryset):
        updated = queryset.exclude(pk=request.user.pk).update(is_active=False)
        skipped = queryset.count() - updated
        msg = f"{updated} کاربر غیرفعال شد."
        if skipped:
            msg += " حساب خودتان برای امنیت تغییر نکرد."
        self.message_user(request, msg)
