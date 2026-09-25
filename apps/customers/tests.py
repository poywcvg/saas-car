"""تست‌های ثبت مشتری: فقط اسم و موبایل کافی است، خودرو اختیاری است."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.businesses.models import Business, Membership
from apps.vehicles.models import VehicleBrand, VehicleModel, VehicleOption

from .models import Customer

User = get_user_model()

# پست خالی بخش خودرو — همان چیزی که مرورگر می‌فرستد وقتی کاربر
# چیزی در فیلدهای خودرو وارد نکرده است.
EMPTY_VEHICLE_POST = {
    "brand": "",
    "model": "",
    "year": "",
    "color": "",
    "fuel": "",
    "plate": "",
    "current_mileage_km": "",
    "service_interval_km": "",
    "service_interval_months": "",
    "preferred_oil": "",
}


class CustomerAddTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester")
        self.business = Business.objects.create(
            name="تعویض روغنی تست", owner=self.user
        )
        Membership.objects.create(
            user=self.user, business=self.business, role=Membership.Role.OWNER
        )
        self.client.force_login(self.user)
        self.url = reverse("customers:add")

    def _messages(self, response):
        return [str(m) for m in response.context["messages"]]

    def test_add_customer_with_only_name_and_phone(self):
        """رگرسیون باگ اصلی: ثبت فقط با اسم و موبایل باید موفق باشد + alert."""
        response = self.client.post(
            self.url,
            {"full_name": "علی رضایی", "phone": "09123456789", **EMPTY_VEHICLE_POST},
            follow=True,
        )
        customer = Customer.objects.get(business=self.business)
        self.assertRedirects(response, reverse("customers:detail", args=[customer.pk]))
        self.assertEqual(customer.vehicles.count(), 0)
        msgs = self._messages(response)
        self.assertTrue(
            any("علی رضایی" in m and "ثبت شد" in m for m in msgs),
            f"پیام موفقیت با اسم مشتری دیده نشد: {msgs}",
        )

    def test_add_customer_with_vehicle(self):
        """وقتی داده‌ی خودرو وارد شده، خودرو هم ثبت شود."""
        # سیگنال ساخت کسب‌وکار، برندها/مدل‌ها/گزینه‌های پیش‌فرض را می‌سازد
        brand = VehicleBrand.objects.get(business=self.business, name="ایران خودرو")
        model = VehicleModel.objects.get(brand=brand, name="پژو ۲۰۶")
        fuel = VehicleOption.objects.get(
            business=self.business, kind=VehicleOption.Kind.FUEL, name="بنزین"
        )
        response = self.client.post(
            self.url,
            {
                "full_name": "سارا محمدی",
                "phone": "09987654321",
                "brand": str(brand.pk),
                "model": str(model.pk),
                "year": "2022",
                "fuel": str(fuel.pk),
                "current_mileage_km": "85000",
                "plate": "",
                "color": "",
                "service_interval_km": "",
                "service_interval_months": "",
                "preferred_oil": "",
            },
            follow=True,
        )
        customer = Customer.objects.get(
            business=self.business, full_name="سارا محمدی"
        )
        self.assertRedirects(response, reverse("customers:detail", args=[customer.pk]))
        self.assertEqual(customer.vehicles.count(), 1)
        msgs = self._messages(response)
        self.assertTrue(
            any("خودرو" in m for m in msgs),
            f"پیام ثبت خودرو دیده نشد: {msgs}",
        )

    def test_partial_vehicle_is_rejected(self):
        """خودروی نصفه (مثلاً فقط سال) خطا بدهد و مشتری ثبت نشود."""
        response = self.client.post(
            self.url,
            {
                "full_name": "نیما کریمی",
                "phone": "09111111111",
                "year": "2020",
                **{k: v for k, v in EMPTY_VEHICLE_POST.items() if k != "year"},
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Customer.objects.filter(business=self.business).exists()
        )
        vform = response.context["vform"]
        self.assertFalse(vform.is_valid())
        self.assertIn("brand", vform.errors)

    def test_missing_phone_is_rejected(self):
        """بدون موبایل ثبت انجام نشود و خطای موبایل نمایش داده شود."""
        response = self.client.post(
            self.url,
            {"full_name": "بدون موبایل", "phone": "", **EMPTY_VEHICLE_POST},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Customer.objects.filter(business=self.business).exists()
        )
        cform = response.context["cform"]
        self.assertFalse(cform.is_valid())
        self.assertIn("phone", cform.errors)

    def test_note_is_optional(self):
        """یادداشت خالی نباید مانع ثبت شود."""
        form_data = {"full_name": "یادداشت خالی", "phone": "09222222222", "note": ""}
        response = self.client.post(
            self.url, {**form_data, **EMPTY_VEHICLE_POST}, follow=True
        )
        self.assertTrue(
            Customer.objects.filter(
                business=self.business, full_name="یادداشت خالی"
            ).exists()
        )
        self.assertEqual(response.status_code, 200)


class CustomerEditTests(TestCase):
    """ویرایش مشتری در /customers/<pk>/edit/ : فقط اسم و موبایل اجباری + alert."""

    def setUp(self):
        self.user = User.objects.create_user(username="editor")
        self.business = Business.objects.create(
            name="تعویض روغنی تست", owner=self.user
        )
        Membership.objects.create(
            user=self.user, business=self.business, role=Membership.Role.OWNER
        )
        self.client.force_login(self.user)
        self.customer = Customer.objects.create(
            business=self.business, full_name="نام قدیمی", phone="09120000000"
        )
        self.url = reverse("customers:edit", args=[self.customer.pk])

    def _messages(self, response):
        return [str(m) for m in response.context["messages"]]

    def test_edit_page_renders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ذخیره تغییرات")

    def test_edit_success_with_alert(self):
        response = self.client.post(
            self.url,
            {"full_name": "نام جدید", "phone": "09333333333", "note": ""},
            follow=True,
        )
        self.assertRedirects(
            response, reverse("customers:detail", args=[self.customer.pk])
        )
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.full_name, "نام جدید")
        self.assertEqual(self.customer.phone, "09333333333")
        msgs = self._messages(response)
        self.assertTrue(
            any("نام جدید" in m and "بروزرسانی شد" in m for m in msgs),
            f"پیام ویرایش با اسم مشتری دیده نشد: {msgs}",
        )

    def test_edit_requires_name_and_phone(self):
        response = self.client.post(
            self.url, {"full_name": "", "phone": "", "note": "x"}
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("full_name", form.errors)
        self.assertIn("phone", form.errors)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.full_name, "نام قدیمی")

    def test_edit_other_business_customer_404(self):
        other_user = User.objects.create_user(username="other")
        other_business = Business.objects.create(
            name="مغازه دیگر", owner=other_user
        )
        Membership.objects.create(
            user=other_user, business=other_business, role=Membership.Role.OWNER
        )
        stranger = Customer.objects.create(
            business=other_business, full_name="غریبه", phone="09444444444"
        )
        response = self.client.get(reverse("customers:edit", args=[stranger.pk]))
        self.assertEqual(response.status_code, 404)
