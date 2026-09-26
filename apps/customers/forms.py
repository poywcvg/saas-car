from django import forms

from core.forms import StyledFormMixin
from core.normalize import normalize_phone

from .models import Customer


class CustomerForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["full_name", "phone", "note"]
        labels = {
            "full_name": "نام و نام خانوادگی",
            "phone": "شماره موبایل",
            "note": "یادداشت",
        }
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "مثلاً: علی رضایی"}),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": "۰۹۱۲۳۴۵۶۷۸۹",
                    "inputmode": "tel",
                    "dir": "ltr",
                }
            ),
            "note": forms.TextInput(
                attrs={"placeholder": "اختیاری — مثلاً: مشتری قدیمی"}
            ),
        }

    def __init__(self, *args, business=None, **kwargs):
        self.business = business
        super().__init__(*args, **kwargs)
        # فقط اسم و موبایل اجباری‌اند؛ بقیه اختیاری.
        self.fields["full_name"].required = True
        self.fields["phone"].required = True
        self.fields["note"].required = False

    def clean_phone(self):
        # ارقام فارسی و پیشوند +98 را یکدست کن: همیشه 09xxxxxxxxx
        phone = normalize_phone(self.cleaned_data.get("phone"))
        if len(phone) != 11 or not phone.startswith("09"):
            raise forms.ValidationError(
                "شماره موبایل درست نیست. ۱۱ رقم و با ۰۹ شروع شود؛ مثل ۰۹۱۲۳۴۵۶۷۸۹"
            )
        # یک شماره فقط یک مشتری در هر کسب‌وکار (جلوگیری از پرونده‌ی تکراری)
        if self.business is not None:
            duplicate = (
                self.business.customers.filter(phone=phone)
                .exclude(pk=self.instance.pk)
                .first()
            )
            if duplicate:
                self.duplicate = duplicate
                raise forms.ValidationError(
                    f"این شماره قبلاً برای «{duplicate.full_name}» ثبت شده است."
                )
        return phone