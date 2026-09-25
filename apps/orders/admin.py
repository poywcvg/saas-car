from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "business", "product", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "business__name", "product__title")
    raw_id_fields = ("user", "business", "product")
