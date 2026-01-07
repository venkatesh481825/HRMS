from django.urls import path
from .views import create_candidate, candidate_onboard

urlpatterns = [
    path('create/', create_candidate),
    path('onboard/<uuid:token>/', candidate_onboard),
]
