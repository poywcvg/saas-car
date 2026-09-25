from django.urls import path

from . import views
from .feeds import LatestPostsFeed


app_name = "blog"


urlpatterns = [
    path("", views.blog_index, name="index"),
    path("rss/", LatestPostsFeed(), name="feed"),
    path("دسته/<str:slug>/", views.category_detail, name="category"),
    path("<str:slug>/", views.post_detail, name="detail"),
]
