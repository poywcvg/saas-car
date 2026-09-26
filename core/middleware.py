"""
میان‌افزار چند-مستأجری (multitenancy) بر پایه‌ی میزبان (Host).

روی میزبان‌های پلتفرم (localhost, charkhyar.ir, ...) رفتار عادی است:
    request.business = None
    request.is_tenant = False

روی ساب‌دامین یا دامنه‌ی اختصاصی یک نماینده:
    request.business = <Business>
    request.is_tenant = True
    request.urlconf  = "config.urls_tenant"   ← نقشه‌ی مسیرهای سایتِ نماینده

میزبان ناشناخته (ساب‌دامینی که به هیچ کسب‌وکاری وصل نیست) → 404.
"""
from django.conf import settings
from django.http import Http404


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.base_domain = settings.TENANT_BASE_DOMAIN.lower()
        self.platform_hosts = {h.lower() for h in settings.PLATFORM_HOSTS}

    def __call__(self, request):
        request.business = None
        request.is_tenant = False

        host = request.get_host().split(":")[0].lower()

        business = self._resolve_business(host)
        if business is not None:
            request.business = business
            request.is_tenant = True
            request.urlconf = "config.urls_tenant"

        return self.get_response(request)

    def _resolve_business(self, host):
        # میزبان صریحِ پلتفرم → بدون مستأجر
        if host in self.platform_hosts:
            return None

        from apps.businesses.models import Business

        # ۱) دامنه‌ی اختصاصی (custom domain) — تطبیق کامل
        business = Business.objects.filter(custom_domain=host).first()
        if business is not None:
            return business

        # ۲) ساب‌دامین روی دامنه‌ی پایه یا روی localhost توسعه
        subdomain = self._extract_subdomain(host)
        if not subdomain:
            return None
        if subdomain in {"www", "app"}:
            return None

        business = Business.objects.filter(subdomain=subdomain).first()
        if business is None:
            # ساب‌دامینِ ناشناخته → صفحه‌ی «یافت نشد»
            raise Http404("این نشانی به هیچ کسب‌وکاری تعلق ندارد.")
        return business

    def _extract_subdomain(self, host):
        """برچسبِ سمت‌چپ را به‌عنوان ساب‌دامین برگردان (فقط یک سطح)."""
        # <sub>.charkhyar.ir
        suffix = "." + self.base_domain
        if host.endswith(suffix):
            label = host[: -len(suffix)]
            return label.split(".")[-1] if label else ""

        # <sub>.localhost  (توسعه)
        if host.endswith(".localhost"):
            label = host[: -len(".localhost")]
            return label.split(".")[-1] if label else ""

        return ""
