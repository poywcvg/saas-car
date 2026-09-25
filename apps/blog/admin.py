from django.contrib import admin

from .models import Category, Post, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "sort_order", "created_at")
    list_editable = ("sort_order",)
    search_fields = ("title", "slug")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("title", "slug")
    search_fields = ("title", "slug")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "status",
        "featured",
        "published_at",
        "reading_minutes",
        "views",
    )
    list_filter = ("status", "featured", "category", "tags")
    search_fields = ("title", "excerpt", "content", "slug")
    filter_horizontal = ("tags",)
    readonly_fields = ("reading_minutes", "views", "created_at", "updated_at")
    fieldsets = (
        ("مشخصات", {"fields": ("title", "slug", "excerpt", "category", "tags")}),
        ("محتوا", {"fields": ("content", "faqs")}),
        (
            "سئو (خالی = خودکار)",
            {
                "fields": ("meta_title", "meta_description", "og_image"),
                "classes": ("collapse",),
            },
        ),
        (
            "انتشار",
            {
                "fields": (
                    "status",
                    "published_at",
                    "featured",
                    "reading_minutes",
                    "views",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
