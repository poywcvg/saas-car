from django import forms

from core.forms import StyledFormMixin

from .models import OilChange


class OilChangeForm(StyledFormMixin, forms.ModelForm):
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
            "service_date": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service_date"].input_formats = ["%Y-%m-%d"]
        self.fields["oil_name"].required = False
        self.fields["note"].required = False
