<div align="right">

# سرویسا (Servisa)

**پلتفرم SaaS باشگاه مشتریان برای کسب‌وکارهای خدمات خودرو**

</div>

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38BDF8?logo=tailwindcss&logoColor=white)
![Status](https://img.shields.io/badge/status-in%20development-orange)

</div>

---

سرویسا یک پلتفرم **چندمستأجری (multi-tenant)** است که به کسب‌وکارهای خدمات خودرو کمک می‌کند مشتریان و خودروهایشان را مدیریت کنند و موعد سرویس‌ها را به‌موقع یادآوری کنند. پلتفرم چندمحصولی است و **«تعویض روغن» نخستین محصولِ فعال (پرچم‌دار)** آن است؛ محصولات دیگر به‌تدریج اضافه می‌شوند.

تمرکز طراحی روی **سادگی و کاربری آسان** است — به‌گونه‌ای که حتی کاربرِ کم‌سواد هم بتواند بدون راهنما با آن کار کند: هر آیکون همراه برچسب فارسی، وضعیت‌ها با «رنگ + آیکون + واژه»، و دکمه‌های بزرگ و روشن.

## ✨ ویژگی‌ها

- 🏢 **چندمستأجری با ساب‌دامین** — هر کسب‌وکار سایت اختصاصی خود را روی `<subdomain>.servisa.ir` دارد
- 👥 **مدیریت مشتریان و خودروها** با جست‌وجوی سریع
- 🛢️ **ثبت تعویض روغن** با ماشین‌حساب زنده‌ی موعد بعدی (بر پایه‌ی کیلومتر یا زمان، هرکدام زودتر برسد)
- 🔔 **یادآوری‌ها** برای خودروهای نزدیک موعد و گذشته از موعد + لینک عمومیِ پیامکی برای مشتری
- 🧩 **کاتالوگ محصولات** (فعال / به‌زودی)
- 🎨 رابط کاربری فارسی و **راست‌به‌چپ (RTL)** با Tailwind CSS و فونت وزیرمتن

## 🛠️ تکنولوژی‌ها

| لایه | ابزار |
|------|-------|
| بک‌اند | Django 5.2 · Python 3.13 |
| پایگاه‌داده | SQLite (توسعه) |
| فرانت‌اند | Tailwind CSS 3.4 · Alpine.js |
| استقرار | Gunicorn (WSGI) |

## 🚀 راه‌اندازی محلی

نیازمندی‌ها: **Python 3.13+** و **Node.js** (برای ساخت CSS).

```bash
# ۱) دریافت پروژه
git clone https://github.com/poywcvg/saas-car.git
cd saas-car

# ۲) محیط مجازی پایتون
python -m venv .venv
# ویندوز:
.venv\Scripts\activate
# لینوکس/مک:
# source .venv/bin/activate

# ۳) نصب وابستگی‌های پایتون
pip install -r requirements.txt

# ۴) متغیرهای محیطی
cp .env.example .env      # سپس مقدار DJANGO_SECRET_KEY را در .env تنظیم کنید

# ۵) وابستگی‌های فرانت‌اند و ساخت CSS
npm install
npm run build:css

# ۶) پایگاه‌داده و اجرا
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

اکنون پلتفرم روی `http://localhost:8000` در دسترس است.

> **تستِ چندمستأجری در توسعه:** ساب‌دامین‌های `*.localhost` روی `127.0.0.1` حل می‌شوند، پس سایت اختصاصی هر کسب‌وکار روی نشانی‌هایی مثل `http://<subdomain>.localhost:8000` قابل مشاهده است.

هنگام کار روی استایل‌ها، به‌جای مرحله‌ی ۵ از حالت watch استفاده کنید:

```bash
npm run watch:css
```

## 🔐 متغیرهای محیطی

| متغیر | توضیح | پیش‌فرض |
|-------|-------|---------|
| `DJANGO_SECRET_KEY` | کلید امنیتی جنگو (در تولید اجباری) | یک کلیدِ ناامنِ توسعه |
| `DJANGO_DEBUG` | حالت دیباگ | `True` |

برای ساخت یک کلید تازه:

```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

## 📁 ساختار پروژه

```
saas-car/
├── apps/
│   ├── accounts/     # احراز هویت و کاربران
│   ├── businesses/   # کسب‌وکارها، داشبورد، یادآوری‌ها
│   ├── catalog/      # کاتالوگ محصولات (خدمات)
│   ├── customers/    # مشتریان و لینک عمومی
│   ├── vehicles/     # خودروها
│   ├── oilchange/    # ثبت تعویض روغن (محصول پرچم‌دار)
│   ├── tenants/      # سایت اختصاصی هر کسب‌وکار
│   └── pages/        # صفحات عمومی (لندینگ)
├── core/             # میدلورِ چندمستأجری، دسترسی، منطق موعد سرویس
├── config/           # تنظیمات و مسیریابی
├── templates/        # قالب‌های Django (RTL فارسی)
└── static/           # منابع Tailwind، فونت‌ها، تصاویر
```

## 📄 مجوز

تمامی حقوق محفوظ است. این یک نرم‌افزارِ اختصاصی است و بدون اجازه‌ی کتبیِ مالک، اجازه‌ی استفاده، کپی یا توزیع داده نمی‌شود.

---

<div align="center">ساخته‌شده با ❤️ برای کسب‌وکارهای خدمات خودرو</div>
