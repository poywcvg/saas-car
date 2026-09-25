"""تست‌های مدیریت اعضای تیم: دسترسی مالک/مدیر/کارمند و محافظ‌ها."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.businesses.models import Business, Membership

User = get_user_model()


class TeamManagementTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", first_name="مالک")
        self.manager = User.objects.create_user(username="manager")
        self.employee = User.objects.create_user(username="employee")
        self.outsider = User.objects.create_user(username="outsider")
        self.business = Business.objects.create(
            name="تعویض روغنی تست", owner=self.owner
        )
        Membership.objects.create(
            user=self.owner, business=self.business, role=Membership.Role.OWNER
        )
        Membership.objects.create(
            user=self.manager, business=self.business, role=Membership.Role.MANAGER
        )
        Membership.objects.create(
            user=self.employee, business=self.business, role=Membership.Role.EMPLOYEE
        )
        self.list_url = reverse("accounts:team")
        self.edit_url = lambda u: reverse("accounts:team_edit", args=[u.pk])
        self.remove_url = lambda u: reverse("accounts:team_remove", args=[u.pk])

    def _msgs(self, response):
        return [str(m) for m in response.context["messages"]]

    # --- دسترسی به لیست ---

    def test_owner_and_manager_can_view_list(self):
        for user in (self.owner, self.manager):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get(self.list_url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "اعضای تیم")
                self.client.logout()

    def test_employee_is_denied_list(self):
        self.client.force_login(self.employee)
        response = self.client.get(self.list_url, follow=True)
        self.assertRedirects(response, reverse("businesses:dashboard"))
        self.assertTrue(any("دسترسی" in m for m in self._msgs(response)))

    def test_outsider_without_business_redirects_to_create(self):
        self.client.force_login(self.outsider)
        response = self.client.get(self.list_url)
        self.assertRedirects(response, reverse("businesses:create"))

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)

    # --- ویرایش مشخصات ---

    def test_manager_can_edit_employee_contact(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            self.edit_url(self.employee),
            {
                "first_name": "کارمند",
                "last_name": "جدید",
                "phone": "۰۹۱۲۳۴۵۶۷۸۹",
                "email": "",
            },
            follow=True,
        )
        self.assertRedirects(response, self.list_url)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.first_name, "کارمند")
        # ارقام فارسی نرمالایز می‌شوند
        self.assertEqual(self.employee.phone, "09123456789")
        self.assertTrue(any("بروز‌رسانی شد" in m or "بروزرسانی شد" in m for m in self._msgs(response)))

    def test_manager_cannot_change_role(self):
        self.client.force_login(self.manager)
        self.client.post(
            self.edit_url(self.employee),
            {
                "first_name": "x",
                "last_name": "y",
                "phone": "09120000000",
                "email": "",
                "role": Membership.Role.OWNER,
            },
        )
        membership = Membership.objects.get(
            user=self.employee, business=self.business
        )
        self.assertEqual(membership.role, Membership.Role.EMPLOYEE)

    def test_owner_can_change_role_and_deactivate(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            self.edit_url(self.employee),
            {
                "first_name": "e",
                "last_name": "e",
                "phone": "09120000001",
                "email": "",
                "role": Membership.Role.MANAGER,
                # is_active نفرستادن = غیرفعال
            },
            follow=True,
        )
        self.assertRedirects(response, self.list_url)
        membership = Membership.objects.get(
            user=self.employee, business=self.business
        )
        self.assertEqual(membership.role, Membership.Role.MANAGER)
        self.employee.refresh_from_db()
        self.assertFalse(self.employee.is_active)

    def test_owner_cannot_demote_self(self):
        # فیلدهای دسترسی برای خودِ کاربر نادیده گرفته می‌شوند؛
        # مشخصات تماس ذخیره و نقش مالک دست‌نخورده می‌ماند.
        self.client.force_login(self.owner)
        response = self.client.post(
            self.edit_url(self.owner),
            {
                "first_name": "o",
                "last_name": "o",
                "phone": "09120000002",
                "email": "",
                "role": Membership.Role.EMPLOYEE,
                # is_active نفرستادن هم نباید خود را غیرفعال کند
            },
            follow=True,
        )
        membership = Membership.objects.get(
            user=self.owner, business=self.business
        )
        self.assertEqual(membership.role, Membership.Role.OWNER)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_active)
        self.assertEqual(self.owner.first_name, "o")
        self.assertTrue(any("بروزرسانی شد" in m for m in self._msgs(response)))

    def test_edit_non_member_404(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.edit_url(self.outsider))
        self.assertEqual(response.status_code, 404)

    def test_edit_page_renders(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.edit_url(self.employee))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ذخیره تغییرات")
        # بخش دسترسی برای ویرایش دیگران دیده می‌شود
        self.assertContains(response, "سطح دسترسی")
        # ... ولی برای خودش نه
        response = self.client.get(self.edit_url(self.owner))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "سطح دسترسی")

    # --- حذف از تیم ---

    def test_owner_can_remove_employee(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.remove_url(self.employee), follow=True)
        self.assertRedirects(response, self.list_url)
        self.assertFalse(
            Membership.objects.filter(
                user=self.employee, business=self.business
            ).exists()
        )
        # حساب کاربری باقی می‌ماند؛ فقط عضویت حذف می‌شود
        self.assertTrue(User.objects.filter(pk=self.employee.pk).exists())
        self.assertTrue(any("حذف شد" in m for m in self._msgs(response)))

    def test_owner_cannot_remove_self(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.remove_url(self.owner), follow=True)
        self.assertTrue(
            Membership.objects.filter(
                user=self.owner, business=self.business
            ).exists()
        )
        self.assertTrue(any("خودتان" in m for m in self._msgs(response)))

    def test_manager_cannot_remove(self):
        self.client.force_login(self.manager)
        response = self.client.post(self.remove_url(self.employee), follow=True)
        self.assertRedirects(response, reverse("businesses:dashboard"))
        self.assertTrue(
            Membership.objects.filter(
                user=self.employee, business=self.business
            ).exists()
        )

    def test_remove_requires_post(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.remove_url(self.employee))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(
            Membership.objects.filter(
                user=self.employee, business=self.business
            ).exists()
        )
