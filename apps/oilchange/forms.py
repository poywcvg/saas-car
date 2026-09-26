import datetime
import re

from django import forms

from core.forms import StyledFormMixin
from core.jalali import jalali_date
from core.normalize import to_ascii_digits

from .models import OilChange
from django.utils import timezone


def parse_service_date(value) -> datetime.date:
    """تاریخ را از ورودی کاربر می‌خواند: شمسی (۱۴۰۵/۷/۳) یا میلادی (2026-09-25).

    سالِ کمتر از ۱۷۰۰ یعنی شمسی. جداکننده می‌تواند / یا - باشد.
    """
    if isinstance(value, datetime.date):
        return value
    text = to_ascii_digits(str(value or "")).strip()
    match = re.fullmatch(r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})", text)
    if not match:
        raise ValueError("bad format")
    y, m, d = (int(part) for part in match.groups())
    if y < 1700:
        return jalali_date(y, m, d)
    return datetime.date(y, m, d)


class OilChangeForm(StyledFormMixin, forms.ModelForm):
    # تاریخ به‌صورت متن دریافت می‌شود تا ورودیِ شمسی (از دکمه‌های امروز/دیروز
    # یا انتخابگرِ روز/ماه/سال) پذیرفته شود؛ در دیتابیس میلادی ذخیره می‌شود.
    service_date = forms.CharField(label="تاریخ تعویض", widget=forms.HiddenInput)

    class Meta:
        model = OilChange
        fields = [
            "service_date",
            "mileage_km",
            "oil_name",
            "interval_km",
            "interval_months",
            "note",
        ]
        widgets = {
            "mileage_km": forms.NumberInput(
                attrs={
                    "placeholder": "مثلاً: ۱۲۰۰۰۰",
                    "inputmode": "numeric",
                    "min": 0,
                    "x-model.number": "mileage",
                }
            ),
            "oil_name": forms.TextInput(
                attrs={"placeholder": "اختیاری — مثلاً: بهران توربین ۲۰W۵۰"}
            ),
            # عدد آزاد: اپراتور می‌تواند از دکمه‌های پیش‌فرض یا مقدار دلخواه بزند
            "interval_km": forms.NumberInput(
                attrs={
                    "inputmode": "numeric",
                    "min": 500,
                    "step": 500,
                    "placeholder": "مثلاً: ۵۰۰۰",
                    "x-ref": "intervalKm",
                    "x-model.number": "intervalKm",
                }
            ),
            "interval_months": forms.Select(
                choices=OilChange.INTERVAL_MONTHS_CHOICES,
                attrs={"x-model.number": "intervalMonths"},
            ),
            "note": forms.TextInput(attrs={"placeholder": "اختیاری"}),
        }

    def __init__(self, *args, vehicle=None, **kwargs):
        self.vehicle = vehicle
        super().__init__(*args, **kwargs)
        self.fields["oil_name"].required = False
        self.fields["note"].required = False

    def clean_service_date(self):
        try:
            value = parse_service_date(self.cleaned_data.get("service_date"))
        except ValueError:
            raise forms.ValidationError("تاریخ درست نیست. روز، ماه و سال را دوباره انتخاب کن.")
        if value > timezone.localdate():
            raise forms.ValidationError("تاریخ نمی‌تواند بعد از امروز باشد.")
        return value

    def clean(self):
        cleaned = super().clean()
        mileage = cleaned.get("mileage_km")
        service_date = cleaned.get("service_date")
        vehicle = self.vehicle
        # کیلومتر نباید از آخرین تعویضِ قبلی کمتر باشد (اشتباهِ رایجِ تایپ)
        if (
            vehicle is not None
            and mileage is not None
            and vehicle.last_mileage_km
            and isinstance(service_date, datetime.date)
            and vehicle.last_service_date
            and service_date >= vehicle.last_service_date
            and mileage < vehicle.last_mileage_km
        ):
            self.add_error(
                "mileage_km",
                f"کیلومتر از دفعه‌ی قبل ({vehicle.last_mileage_km:,}) کمتر است. "
                "عدد کیلومترشمار را دوباره نگاه کن.",
            )
        return cleaned
