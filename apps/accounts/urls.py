from django.urls import path

from . import views


app_name = "accounts"


urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("login/otp/", views.otp_login, name="otp_login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("team/", views.team_list, name="team"),
    path("team/<int:pk>/", views.team_member_edit, name="team_edit"),
    path("team/<int:pk>/remove/", views.team_member_remove, name="team_remove"),
    path("send-otp/", views.send_otp, name="send_otp"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
]
