from django import forms

from apps.businesses.models import Membership
from core.forms import StyledFormMixin

from .models import Order


class OrderForm(StyledFormMixin, forms.ModelForm):
    business = forms.ModelChoiceField(
        queryset=Membership.objects.none(),
        label="فروشگاه",
        empty_label="انتخاب کنید…",
        to_field_name="business_id",
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
            memberships = Membership.objects.filter(user=user).select_related("business")
            self.fields["business"].queryset = memberships
            self.fields["business"].label_from_instance = lambda m: m.business.name

    def save(self, commit=True):
        order = super().save(commit=False)
        order.user = self.user
        order.product = self.product
        membership = self.cleaned_data["business"]
        order.business = membership.business
        if commit:
            order.save()
        return order
