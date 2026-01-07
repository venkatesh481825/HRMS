from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from accounts.models import UserRole

def home(request):
    """Landing page for the HRMS Onboarding System"""
    return render(request, 'home.html')

@login_required
def login_redirect(request):
    """Redirect users based on their role after login"""
    if hasattr(request.user, 'userprofile'):
        role = request.user.userprofile.role
        if role == UserRole.HR:
            return redirect('hr_dashboard')
        elif role == UserRole.EMPLOYEE:
            return redirect('employee_dashboard')
        elif role == UserRole.ADMIN:
            return redirect('employee_dashboard')
        elif role in [UserRole.MANAGER, UserRole.SUPERADMIN]:
            return redirect('employee_dashboard')
    # Default redirect for employees
    return redirect('employee_dashboard')

@login_required
def employee_dashboard(request):
    """Employee dashboard - main HRMS application"""
    return render(request, 'accounts/employee_dashboard.html')

def logout_view(request):
    """Custom logout view that handles both GET and POST"""
    logout(request)
    return redirect('/')
