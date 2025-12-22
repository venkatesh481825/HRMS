from django.contrib import admin
from .models import Attendance, Permission, Regularization


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "date",
        "status",
        "check_in_time",
        "check_out_time",
        "working_hours",
        "source",
    )
    list_filter = ("status", "source", "date")
    search_fields = ("employee__username", "employee__email")
    readonly_fields = ("working_hours", "created_at")
    ordering = ("-date",)
    date_hierarchy = "date"


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "date",
        "from_time",
        "to_time",
        "status",
        "approved_by",
    )
    list_filter = ("status", "date")
    search_fields = ("employee__username",)
    readonly_fields = ("created_at",)
    ordering = ("-date",)


@admin.register(Regularization)
class RegularizationAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "attendance",
        "status",
        "approved_by",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("employee__username",)
    readonly_fields = ("created_at",)
