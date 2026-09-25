from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

from apps.businesses.models import Membership
from core.forms import StyledFormMixin


User = get_user_model()


class LoginForm(StyledFormMixin, AuthenticationForm):
    """فرم ورود با ظاهر یکدست."""

    error_messages = {
        "invalid_login": "نام کاربری یا رمز عبور اشتباه است.",
        "inactive": "این حساب غیرفعال است.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "نام کاربری"
        self.fields["password"].label = "رمز عبور"


class RegisterForm(StyledFormMixin, forms.ModelForm):
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput,
        min_length=8,
        help_text="حداقل ۸ کاراکتر.",
    )

    password_confirm = forms.CharField(
        label="تکرار رمز عبور",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "phone",
            "email",
        ]

        labels = {
            "username": "نام کاربری",
            "first_name": "نام",
            "last_name": "نام خانوادگی",
            "phone": "شماره موبایل",
            "email": "ایمیل",
        }

    def clean_password_confirm(self):
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("رمز عبور و تکرار آن یکسان نیستند.")

        return password_confirm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = ""
        self.fields["email"].required = False

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "email"]
        labels = {
            "first_name": "نام",
            "last_name": "نام خانوادگی",
            "phone": "شماره موبایل",
            "email": "ایمیل",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "نام"}),
            "last_name": forms.TextInput(attrs={"placeholder": "نام خانوادگی"}),
            "phone": forms.TextInput(attrs={"placeholder": "شماره موبایل"}),
            "email": forms.EmailInput(attrs={"placeholder": "ایمیل"}),
        }


class PhoneForm(StyledFormMixin, forms.Form):
    phone = forms.CharField(
        label="شماره موبایل",
        max_length=15,
        widget=forms.TextInput(attrs={"placeholder": "۰۹۱۲۱۲۳۴۵۶۷", "dir": "ltr"}),
    )


class OTPForm(StyledFormMixin, forms.Form):
    code = forms.CharField(
        label="کد تایید",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={"placeholder": "۱۲۳۴۵۶", "dir": "ltr", "inputmode": "numeric"}),
    )


def normalize_phone(value):
    """ارقام فارسی/عربی به لاتین + فقط ارقام؛ خالی → None."""
    phone = (value or "").strip()
    if not phone:
        return None
    translation = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    digits = "".join(ch for ch in phone.translate(translation) if ch.isdigit())
    return digits


class MemberEditForm(StyledFormMixin, forms.ModelForm):
    """ویرایش مشخصات یک عضو تیم توسط مالک/مدیر (نام، موبایل، ایمیل)."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "email"]
        labels = {
            "first_name": "نام",
            "last_name": "نام خانوادگی",
            "phone": "شماره موبایل",
            "email": "ایمیل",
        }
        widgets = {
            "phone": forms.TextInput(
                attrs={"placeholder": "۰۹۱۲۳۴۵۶۷۸۹", "inputmode": "tel", "dir": "ltr"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = False

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone"))
        if phone is not None and len(phone) < 10:
            raise forms.ValidationError("شماره موبایل معتبر نیست.")
        return phone


class MemberRoleForm(StyledFormMixin, forms.ModelForm):
    """تغییر نقش عضو در تیم — فقط مالک."""

    class Meta:
        model = Membership
        fields = ["role"]
        labels = {"role": "نقش در تیم"}
