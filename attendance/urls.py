from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [

    # Employee attendance
    path("check-in/", views.check_in, name="check_in"),
    path("check-out/", views.check_out, name="check_out"),
    path("my-attendance/", views.my_attendance, name="my_attendance"),

    # Permission
    path("permission/apply/", views.apply_permission, name="apply_permission"),
    path("permission/approve/<int:pk>/", views.approve_permission, name="approve_permission"),

    # Regularization
    path("regularization/apply/<int:attendance_id>/", views.apply_regularization, name="apply_regularization"),
    path("regularization/approve/<int:pk>/", views.approve_regularization, name="approve_regularization"),
]
