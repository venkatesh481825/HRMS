from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import Attendance, Permission, Regularization

def is_hr_or_admin(user):
    return user.is_staff or user.is_superuser


@login_required
def check_in(request):
    today = timezone.now().date()

    attendance, created = Attendance.objects.get_or_create(
        employee=request.user,
        date=today,
        defaults={"status": "PRESENT", "source": "AUTO"},
    )

    if attendance.check_in_time:
        return redirect("attendance:my_attendance")

    attendance.check_in_time = timezone.now()
    attendance.status = "HALF_DAY"
    attendance.save()

    return redirect("attendance:my_attendance")



@login_required
def check_out(request):
    today = timezone.now().date()

    attendance = get_object_or_404(
        Attendance,
        employee=request.user,
        date=today
    )

    if not attendance.check_in_time or attendance.check_out_time:
        return redirect("attendance:my_attendance")

    attendance.check_out_time = timezone.now()
    attendance.working_hours = attendance.calculate_working_hours()
    attendance.status = "PRESENT"
    attendance.save()

    return redirect("attendance:my_attendance")



@login_required
def my_attendance(request):
    records = Attendance.objects.filter(employee=request.user)
    return render(request, "attendance/my_attendance.html", {"records": records})


@login_required
def apply_permission(request):
    if request.method == "POST":
        Permission.objects.create(
            employee=request.user,
            date=request.POST.get("date"),
            from_time=request.POST.get("from_time"),
            to_time=request.POST.get("to_time"),
            reason=request.POST.get("reason"),
        )
        return redirect("attendance:my_attendance")

    return render(request, "attendance/apply_permission.html")



@login_required
def approve_permission(request, pk):
    if not is_hr_or_admin(request.user):
        raise PermissionDenied

    permission = get_object_or_404(Permission, pk=pk)
    permission.status = "APPROVED"
    permission.approved_by = request.user
    permission.save()

    return redirect("/admin/attendance/permission/")



@login_required
def apply_regularization(request, attendance_id):
    attendance = get_object_or_404(
        Attendance,
        id=attendance_id,
        employee=request.user
    )

    if request.method == "POST":
        Regularization.objects.create(
            attendance=attendance,
            employee=request.user,
            requested_check_in=request.POST.get("check_in"),
            requested_check_out=request.POST.get("check_out"),
            reason=request.POST.get("reason"),
        )
        return redirect("attendance:my_attendance")

    return render(
        request,
        "attendance/apply_regularization.html",
        {"attendance": attendance}
    )




@login_required
def approve_regularization(request, pk):
    if not is_hr_or_admin(request.user):
        raise PermissionDenied

    reg = get_object_or_404(Regularization, pk=pk)

    attendance = reg.attendance
    attendance.check_in_time = reg.requested_check_in
    attendance.check_out_time = reg.requested_check_out
    attendance.working_hours = attendance.calculate_working_hours()
    attendance.status = "PRESENT"
    attendance.source = "REGULARIZED"
    attendance.save()

    reg.status = "APPROVED"
    reg.approved_by = request.user
    reg.save()

    return redirect("/admin/attendance/regularization/")
