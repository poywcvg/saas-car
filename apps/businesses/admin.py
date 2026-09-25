from django.contrib import admin

from .models import Business, Membership


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "is_listed", "owner", "created_at")
    list_filter = ("city", "is_listed")
    search_fields = ("name", "city", "owner__username")
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "business", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "business__name")
