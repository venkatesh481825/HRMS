from django.contrib import admin

from .models import Attendance

# Register your models here.

admin.site.register(Attendance)

class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'date',
        'check_in',
        'check_out',
        'status'
    )

    list_filter = (
        'status',
        'date'
    )

    search_fields = (
        'employee__username',
        'employee__first_name',
        'employee__last_name'
    )

    ordering = ('-date',)

    readonly_fields = (
        'created_at',
        'updated_at'
    )