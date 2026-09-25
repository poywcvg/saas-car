import random
import string

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    phone = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        verbose_name="شماره موبایل",
    )

    def __str__(self):
        return self.username


class OTP(models.Model):
    phone = models.CharField(
        max_length=15,
        verbose_name="شماره موبایل",
    )

    code = models.CharField(
        max_length=6,
        verbose_name="کد تایید",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )

    expires_at = models.DateTimeField(
        verbose_name="تاریخ انقضا",
    )

    is_used = models.BooleanField(
        default=False,
        verbose_name="استفاده شده",
    )

    class Meta:
        verbose_name = "کد تایید"
        verbose_name_plural = "کدهای تایید"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.phone} — {self.code}"

    @classmethod
    def generate(cls, phone, expires_in_minutes=5):
        code = "".join(random.choices(string.digits, k=6))
        now = timezone.now()
        return cls.objects.create(
            phone=phone,
            code=code,
            expires_at=now + timezone.timedelta(minutes=expires_in_minutes),
        )

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=["is_used"])