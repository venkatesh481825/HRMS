"""
URL configuration for hrms_onboarding project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from accounts.views import home, login_redirect, logout_view, employee_dashboard

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', logout_view, name='logout'),
    path('accounts/redirect/', login_redirect, name='login_redirect'),
    path('employee/dashboard/', employee_dashboard, name='employee_dashboard'),
    path('candidate/', include('candidate.urls')),
    path('documents/', include('documents.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

