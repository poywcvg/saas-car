"""نمایش‌های عمومی وبلاگ: فهرست، دسته‌بندی و صفحه‌ی مقاله.

نکته‌های سئو در همین‌جا رعایت شده: canonical تمیز برای صفحه‌بندی،
noindex برای نتایج جست‌وجو (محتوای تکراری/نازک)، و داده‌ی ساختاریافته‌ی
Blog / BlogPosting / Breadcrumb / FAQ در هر صفحه.
"""

from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.safestring import mark_safe

from core import seo

from .models import Category, Post

POSTS_PER_PAGE = 9


def _published_filter():
    """شرط «منتشرشده و موعد انتشار رسیده» برای annotateها."""
    now = timezone.now()
    return Q(posts__status=Post.Status.PUBLISHED) & (
        Q(posts__published_at__isnull=True) | Q(posts__published_at__lte=now)
    )


def _categories_with_counts():
    """دسته‌های دارای مقاله‌ی منتشرشده، همراه تعداد (برای ناوبری وبلاگ)."""
    return list(
        Category.objects.annotate(n=Count("posts", filter=_published_filter()))
        .filter(n__gt=0)
        .order_by("sort_order", "id")
    )


def _canonical(base_path, page_number):
    """صفحه‌ی ۱ بدون کوئری؛ صفحه‌های بعد با ?page=N (خود-متعارف)."""
    if page_number and page_number > 1:
        return seo.absolute_url(f"{base_path}?page={page_number}")
    return seo.absolute_url(base_path)


def blog_index(request):
    """فهرست مقالات + مقاله‌ی ویژه + جست‌وجو + صفحه‌بندی."""
    q = request.GET.get("q", "").strip()
    base = Post.published.select_related("category").prefetch_related("tags")
    if q:
        base = base.filter(
            Q(title__icontains=q)
            | Q(excerpt__icontains=q)
            | Q(content__icontains=q)
        )

    featured = None
    if not q:
        featured = base.filter(featured=True).first()

    rest = base.exclude(pk=featured.pk) if featured else base
    paginator = Paginator(rest, POSTS_PER_PAGE)
    page = paginator.get_page(request.GET.get("page"))

    context = {
        "featured": featured if page.number == 1 else None,
        "posts": page,
        "categories": _categories_with_counts(),
        "q": q,
        # نتایج جست‌وجو ایندکس نشوند (جلوگیری از محتوای تکراری در گوگل)
        "robots_noindex": bool(q),
        "canonical": _canonical("/blog/", page.number if not q else 0),
        "jsonld_crumbs": seo.json_ld(
            seo.breadcrumb_ld([("سرویسا", "/"), ("وبلاگ", "/blog/")])
        ),
        "jsonld_blog": seo.json_ld(
            seo.blog_index_ld(list(page.object_list[:5]), seo.absolute_url("/blog/"))
        ),
    }
    return render(request, "blog/index.html", context)


def category_detail(request, slug):
    """صفحه‌ی یک دسته‌بندی با مقالاتش."""
    category = get_object_or_404(Category, slug=slug)
    qs = (
        Post.published.filter(category=category)
        .select_related("category")
        .prefetch_related("tags")
    )
    paginator = Paginator(qs, POSTS_PER_PAGE)
    page = paginator.get_page(request.GET.get("page"))

    context = {
        "category": category,
        "posts": page,
        "categories": _categories_with_counts(),
        "canonical": _canonical(category.get_absolute_url(), page.number),
        "jsonld_crumbs": seo.json_ld(
            seo.breadcrumb_ld(
                [
                    ("سرویسا", "/"),
                    ("وبلاگ", "/blog/"),
                    (category.title, category.get_absolute_url()),
                ]
            )
        ),
        "jsonld_blog": seo.json_ld(
            seo.blog_index_ld(
                list(page.object_list[:5]),
                seo.absolute_url(category.get_absolute_url()),
                name=f"{category.title} — وبلاگ سرویسا",
            )
        ),
    }
    return render(request, "blog/category.html", context)


def post_detail(request, slug):
    """صفحه‌ی مقاله: فهرست، مقاله‌های مرتبط، قبلی/بعدی و FAQ."""
    post = get_object_or_404(
        Post.published.select_related("category").prefetch_related("tags"),
        slug=slug,
    )
    # شمارنده‌ی بازدید (تک‌پرس‌وجوی اتمیک؛ نمایش یک واحد جلوتر)
    Post.objects.filter(pk=post.pk).update(views=models.F("views") + 1)
    post.views += 1

    headings = post.headings()
    related = post.related_posts()
    newer, older = post.neighbors()
    url = seo.absolute_url(post.get_absolute_url())

    faqs = [f for f in (post.faqs or []) if f.get("q") and f.get("a")]

    jsonld_parts = [
        seo.json_ld(seo.blog_post_ld(post, url)),
        seo.json_ld(
            seo.breadcrumb_ld(
                [
                    ("سرویسا", "/"),
                    ("وبلاگ", "/blog/"),
                    (post.category.title, post.category.get_absolute_url()),
                    (post.title, post.get_absolute_url()),
                ]
            )
        ),
    ]
    if faqs:
        jsonld_parts.append(
            seo.json_ld(seo.faq_ld([(f["q"], f["a"]) for f in faqs]))
        )

    context = {
        "post": post,
        "headings": headings,
        "related": related,
        "newer": newer,
        "older": older,
        "faqs": faqs,
        "categories": _categories_with_counts(),
        "canonical": url,
        # اجزا از core.seo.json_ld قبلاً امن شده‌اند؛ اتصالشان هم امن می‌ماند
        "jsonld_all": mark_safe("".join(str(part) for part in jsonld_parts)),
    }
    return render(request, "blog/detail.html", context)
