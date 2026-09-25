from django.contrib import admin

from .models import OilChange


@admin.register(OilChange)
class OilChangeAdmin(admin.ModelAdmin):
    list_display = (
        "vehicle",
        "service_date",
        "mileage_km",
        "next_due_date",
        "next_due_km",
        "created_by",
    )
    list_filter = ("service_date", "vehicle__customer__business")
    search_fields = ("vehicle__title", "vehicle__customer__full_name", "oil_name")
    readonly_fields = ("next_due_km", "next_due_date", "created_at")
