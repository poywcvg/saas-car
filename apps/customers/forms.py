from django import forms

from core.forms import StyledFormMixin

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # فقط اسم و موبایل اجباری‌اند؛ بقیه اختیاری.
        self.fields["full_name"].required = True
        self.fields["phone"].required = True
        self.fields["note"].required = False

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        # ارقام فارسی را به لاتین تبدیل کن تا ذخیره‌ی یکدست شود
        translation = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
        phone = phone.translate(translation)
        digits = "".join(ch for ch in phone if ch.isdigit())
        if len(digits) < 10:
            raise forms.ValidationError("شماره موبایل معتبر نیست.")
        return digits
