from django.db import models
from django.contrib.auth.models import User

class Attendance(models.Model):

    PRESENT = 'P'
    ABSENT = 'A'
    LEAVE = 'L'
    HALF_DAY = 'H'

    STATUS_CHOICES = (
        (PRESENT, 'Present'),
        (ABSENT, 'Absent'),
        (LEAVE, 'Leave'),
        (HALF_DAY, 'Half Day'),
    )

    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default=ABSENT
    )
    remarks = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'date')

    def __str__(self):
        return f"{self.employee.username} - {self.date}"
