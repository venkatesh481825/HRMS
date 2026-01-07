from django.contrib import admin
from .models import Candidate, CandidateToken

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('email', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('email',)

@admin.register(CandidateToken)
class CandidateTokenAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'token', 'is_used', 'expires_at')
