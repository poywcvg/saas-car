from django.contrib import admin

from apps.vehicles.models import Vehicle

from .models import Customer


class VehicleInline(admin.TabularInline):
    model = Vehicle
    extra = 0
    fields = ("title", "plate", "last_service_date", "next_due_date")
    readonly_fields = ("last_service_date", "next_due_date")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "business", "created_at")
    list_filter = ("business",)
    search_fields = ("full_name", "phone")
    inlines = [VehicleInline]
    readonly_fields = ("public_token", "created_at", "updated_at")
