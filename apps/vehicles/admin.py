from django.contrib import admin

from apps.oilchange.models import OilChange

from .models import Vehicle, VehicleBrand, VehicleModel, VehicleOption


class VehicleModelInline(admin.TabularInline):
    model = VehicleModel
    extra = 0
    fields = ("name", "sort_order", "is_active")


@admin.register(VehicleBrand)
class VehicleBrandAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    list_filter = ("business", "is_active")
    search_fields = ("name",)
    inlines = [VehicleModelInline]


@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    list_filter = ("brand__business", "is_active")
    search_fields = ("name", "brand__name")
    autocomplete_fields = ("brand",)


@admin.register(VehicleOption)
class VehicleOptionAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "business", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    list_filter = ("business", "kind", "is_active")
    search_fields = ("name",)


class OilChangeInline(admin.TabularInline):
    model = OilChange
    extra = 0
    fields = ("service_date", "mileage_km", "oil_name", "next_due_date", "next_due_km")
    readonly_fields = ("next_due_date", "next_due_km")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("title", "brand", "model", "year", "plate", "customer", "next_due_date")
    list_filter = ("customer__business", "brand", "fuel")
    search_fields = ("title", "plate", "customer__full_name")
    autocomplete_fields = ("brand", "model", "color", "fuel", "preferred_oil")
    inlines = [OilChangeInline]
