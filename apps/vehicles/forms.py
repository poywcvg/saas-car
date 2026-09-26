from django import forms

from core.forms import StyledFormMixin

from .models import Vehicle, VehicleBrand, VehicleModel, VehicleOption
from django.utils import timezone


INTERVAL_MONTHS_CHOICES = [
    (2, "۲ ماه"),
    (3, "۳ ماه"),
    (4, "۴ ماه"),
    (6, "۶ ماه"),
    (12, "۱۲ ماه"),
]


class VehicleForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "brand",
            "model",
            "year",
            "color",
            "fuel",
            "plate",
            "current_mileage_km",
            "service_interval_km",
            "service_interval_months",
            "preferred_oil",
        ]
        widgets = {
            "plate": forms.TextInput(
                attrs={"placeholder": "اختیاری — مثلاً: ۱۲ ب ۳۴۵ | ۶۸"}
            ),
            "current_mileage_km": forms.NumberInput(
                attrs={
                    "placeholder": "مثلاً ۸۵۰۰۰",
                    "inputmode": "numeric",
                    "min": 0,
                }
            ),
            "service_interval_km": forms.NumberInput(
                attrs={
                    "placeholder": "مثلاً ۵۰۰۰",
                    "inputmode": "numeric",
                    "min": 500,
                    "step": 500,
                }
            ),
            "service_interval_months": forms.Select(
                choices=[("", "پیش‌فرض")] + INTERVAL_MONTHS_CHOICES
            ),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.business = business

        # لیست‌های قابل‌انتخاب را به کسب‌وکار و گزینه‌های فعال محدود کن
        brands = VehicleBrand.objects.none()
        models = VehicleModel.objects.none()
        colors = VehicleOption.objects.none()
        fuels = VehicleOption.objects.none()
        oils = VehicleOption.objects.none()
        if business is not None:
            brands = VehicleBrand.objects.filter(
                business=business, is_active=True
            )
            models = VehicleModel.objects.filter(
                brand__business=business, is_active=True
            ).select_related("brand")
            colors = VehicleOption.objects.filter(
                business=business,
                kind=VehicleOption.Kind.COLOR,
                is_active=True,
            )
            fuels = VehicleOption.objects.filter(
                business=business,
                kind=VehicleOption.Kind.FUEL,
                is_active=True,
            )
            oils = VehicleOption.objects.filter(
                business=business,
                kind=VehicleOption.Kind.OIL,
                is_active=True,
            )

        self.fields["brand"].queryset = brands
        self.fields["model"].queryset = models
        self.fields["color"].queryset = colors
        self.fields["fuel"].queryset = fuels
        self.fields["preferred_oil"].queryset = oils

        self.fields["brand"].empty_label = "انتخاب برند…"
        self.fields["model"].empty_label = "اول برند را انتخاب کن…"
        self.fields["color"].empty_label = "انتخاب رنگ…"
        self.fields["fuel"].empty_label = "انتخاب سوخت…"
        self.fields["preferred_oil"].empty_label = "بدون پیش‌فرض"

        # همه‌ی مشخصات خودرو اختیاری است (فقط اسم و موبایل مشتری الزامی‌اند)
        self.fields["current_mileage_km"].required = False

        # در دراپ‌داون فقط نام گزینه نمایش داده شود (نه «رنگ: سفید»)
        self.fields["color"].label_from_instance = lambda o: o.name
        self.fields["fuel"].label_from_instance = lambda o: o.name
        self.fields["preferred_oil"].label_from_instance = lambda o: o.name
        self.fields["brand"].label_from_instance = lambda o: o.name

        # سال ساخت: بازه‌ی معقول (ورودی عددی)
        this_year = timezone.localdate().year
        self.fields["year"].widget.attrs.update(
            {"placeholder": f"مثلاً {this_year}", "min": 1980, "max": this_year + 1}
        )

        # نگاشت برند → مدل‌ها برای دراپ‌داون وابسته در قالب (Alpine)
        self.models_by_brand = {}
        for m in models:
            self.models_by_brand.setdefault(m.brand_id, []).append(
                {"id": m.id, "name": m.name}
            )

    def clean_current_mileage_km(self):
        # خالی = کیلومتر قبلی (یا ۰ برای خودروی تازه)؛ ستون null نمی‌پذیرد
        value = self.cleaned_data.get("current_mileage_km")
        if value is None:
            return self.instance.current_mileage_km or 0
        return value

    def clean(self):
        cleaned = super().clean()
        brand = cleaned.get("brand")
        model = cleaned.get("model")
        if model and brand and model.brand_id != brand.id:
            self.add_error("model", "این مدل برای برند انتخاب‌شده نیست.")
        if model and not brand:
            self.add_error("brand", "اول برند را انتخاب کن.")
        return cleaned
