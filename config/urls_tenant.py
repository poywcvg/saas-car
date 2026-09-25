"""
نقشه‌ی مسیرهای «سایتِ نماینده» — وقتی درخواست روی ساب‌دامین یک کسب‌وکار است.

TenantMiddleware با ست‌کردن request.urlconf این فایل را جایگزین config.urls می‌کند.

ساختار:
    /                → ویترین/لندینگِ نماینده (با برند خودش)
    /lookup/         → پورتال مشتری (جست‌وجو با موبایل/پلاک، بدون ورود)
    /c/<token>/      → لینک عمومیِ پیامکیِ مشتری (بدون ورود)
    /accounts/ ...   → ورود/خروجِ پنل
    /businesses/ ... → داشبورد و یادآوری‌ها  ┐
    /customers/ ...  → مشتریان               │ پنل ادمینِ نماینده
    /vehicles/ ...   │ خودروها               │ (namespaceها بدون تغییر،
    /oilchange/ ...  │ تعویض روغن            │  پس قالب‌های موجود کار می‌کنند)
    /products/ ...   → محصولات               ┘
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from apps.customers import views as customers_views

urlpatterns = [
    # سایت عمومیِ نماینده
    path("", include("apps.tenants.urls")),

    # پنل ادمینِ نماینده (همان namespaceهای قبلی)
    path("accounts/", include("apps.accounts.urls")),
    path("businesses/", include("apps.businesses.urls")),
    path("products/", include("apps.catalog.urls")),
    path("customers/", include("apps.customers.urls")),
    path("vehicles/", include("apps.vehicles.urls")),
    path("oilchange/", include("apps.oilchange.urls")),

    # لینک عمومی مشتری (پیامکی، بدون ورود)
    path("c/<uuid:token>/", customers_views.public_customer, name="public_customer"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
