from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "slug", "is_available", "is_flagship", "sort_order")
    list_editable = ("is_available", "is_flagship", "sort_order")
    list_filter = ("is_available", "is_flagship", "business")
    search_fields = ("title", "slug")
    autocomplete_fields = ("business",)
