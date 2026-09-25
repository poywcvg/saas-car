"""فید RSS وبلاگ (برای خبرخوان‌ها و کشف سریع مقالات تازه)."""

from django.contrib.syndication.views import Feed

from .models import Post


class LatestPostsFeed(Feed):
    title = "وبلاگ سرویسا — نگهداری خودرو و تعویض روغن"
    link = "/blog/"
    description = (
        "آموزش‌های کاربردی نگهداری خودرو، روغن موتور، فیلتر و سرویس دوره‌ای."
    )

    def items(self):
        return list(
            Post.published.select_related("category")[:15]
        )

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_pubdate(self, item):
        return item.published_at or item.created_at

    def item_updateddate(self, item):
        return item.updated_at

    def item_categories(self, item):
        return [item.category.title]
