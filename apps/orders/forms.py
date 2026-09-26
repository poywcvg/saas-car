from django import forms

from apps.businesses.models import Business
from core.forms import StyledFormMixin

from .models import Order


class OrderForm(StyledFormMixin, forms.ModelForm):
    # فقط کسب‌وکارهایی که کاربر عضوشان است؛ مستقیم Business برمی‌گرداند
    # تا ModelForm بتواند آن را روی Order.business بگذارد.
    business = forms.ModelChoiceField(
        queryset=Business.objects.none(),
        label="فروشگاه",
        empty_label="انتخاب کنید…",
    )

    class Meta:
        model = Order
        fields = ["business", "note"]
        labels = {"note": "یادداشت"}
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3, "placeholder": "اختیاری…"}),
        }

    def __init__(self, user=None, product=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.product = product

        if user:
            businesses = Business.objects.filter(memberships__user=user).distinct()
            self.fields["business"].queryset = businesses
            self.fields["business"].label_from_instance = lambda b: b.name
            # یک مغازه = از قبل انتخاب شده، کاربر لازم نیست کاری کند
            if not self.is_bound and len(businesses) == 1:
                self.initial["business"] = businesses[0].pk

    def save(self, commit=True):
        order = super().save(commit=False)
        order.user = self.user
        order.product = self.product
        if commit:
            order.save()
        return order
