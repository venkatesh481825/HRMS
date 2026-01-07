from django.urls import path
from .views import upload_document, verify_document, hr_dashboard, send_login_credentials

urlpatterns = [
    path('upload/<uuid:token>/', upload_document, name='upload_document'),
    path('hr/dashboard/', hr_dashboard, name='hr_dashboard'),
    path('verify/<int:doc_id>/', verify_document, name='verify_document'),
    path('hr/send-credentials/<int:candidate_id>/', send_login_credentials, name='send_login_credentials'),
]