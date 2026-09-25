"""ابزارهای مشترک فرم‌ها — استایل‌دهی یکدست به همه‌ی فیلدها با Tailwind."""

from django import forms


class StyledFormMixin:
    """کلاس‌های Tailwind را به‌صورت خودکار به ویجت‌های فرم اضافه می‌کند.

    روی هر فرم/ModelForm بگذارید تا فیلدها ظاهر یکدست بگیرند، بدون اینکه
    لازم باشد در تمپلیت دستی رندر شوند.
    """

    #: نوع ویجت‌هایی که کلاس مخصوص خودشان را می‌گیرند
    _TEXT_INPUTS = (
        forms.TextInput,
        forms.NumberInput,
        forms.EmailInput,
        forms.URLInput,
        forms.PasswordInput,
        forms.Textarea,
        forms.DateInput,
        forms.TimeInput,
        forms.DateTimeInput,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            existing = widget.attrs.get("class", "")

            if isinstance(widget, forms.Select):
                base = "input"
            elif isinstance(widget, forms.CheckboxInput):
                base = (
                    "h-5 w-5 rounded border-slate-300 text-brand-600 "
                    "focus:ring-brand-500"
                )
            elif isinstance(widget, self._TEXT_INPUTS):
                base = "input"
            else:
                base = "input"

            widget.attrs["class"] = f"{existing} {base}".strip()

            # placeholder پیش‌فرض از روی برچسب اگر تعیین نشده باشد
            if isinstance(widget, self._TEXT_INPUTS):
                widget.attrs.setdefault("placeholder", field.label or "")
