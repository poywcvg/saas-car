from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from apps.customers import views as customers_views
from apps.pages import seo_views, views as pages_views

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", pages_views.home, name="home"),

    # --- سئو ---
    # کلمه‌ی کلیدی داخل خودِ نشانی: /تعویض-روغنی/کرمان/
    path("تعویض-روغنی/<str:city>/", seo_views.city_directory, name="city_directory"),
    path("robots.txt", seo_views.robots_txt, name="robots_txt"),
    path("sitemap.xml", seo_views.sitemap_xml, name="sitemap_xml"),

    # وبلاگ آموزشی (سئو-محور، فقط روی هاست پلتفرم)
    path("blog/", include("apps.blog.urls")),

    path("accounts/", include("apps.accounts.urls")),

    path("businesses/", include("apps.businesses.urls")),

    path("products/", include("apps.catalog.urls")),

    path("customers/", include("apps.customers.urls")),

    path("vehicles/", include("apps.vehicles.urls")),

    path("garage/", include("apps.vehicles.settings_urls")),

    path("oilchange/", include("apps.oilchange.urls")),

    path("orders/", include("apps.orders.urls")),

    # لینک عمومی مشتری (پیامکی، بدون ورود)
    path("c/<uuid:token>/", customers_views.public_customer, name="public_customer"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
