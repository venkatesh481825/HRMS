from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'document_type', 'status', 'uploaded_at')
    list_filter = ('status',)
    search_fields = ('candidate__email', 'document_type')
