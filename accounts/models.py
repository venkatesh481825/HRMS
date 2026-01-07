from django.db import models
from django.contrib.auth.models import User

class UserRole(models.TextChoices):
    SUPERADMIN = "SUPERADMIN", "Super Admin"
    HR = "HR", "HR"
    MANAGER = "MANAGER", "Manager"
    ADMIN = "ADMIN", "Admin"
    EMPLOYEE = "EMPLOYEE", "Employee"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=UserRole.choices)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
