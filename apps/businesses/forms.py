from django import forms

from core.forms import StyledFormMixin

from .models import Business


class BusinessForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Business
        fields = ["name"]
        labels = {"name": "نام کسب‌وکار"}
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "مثلاً: تعویض‌روغنی مرکزی"}
            ),
        }
