from django.db import models
import uuid
from django.utils import timezone
from datetime import timedelta

class CandidateStatus(models.TextChoices):
    INVITED = "INVITED", "Invited"
    PROFILE_COMPLETED = "PROFILE_COMPLETED", "Profile Completed"

class Candidate(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)

    # Optional file fields to allow candidates to upload multiple documents
    document_1 = models.FileField(upload_to="documents/", blank=True, null=True)
    document_2 = models.FileField(upload_to="documents/", blank=True, null=True)
    document_3 = models.FileField(upload_to="documents/", blank=True, null=True)

    status = models.CharField(
        max_length=30,
        choices=CandidateStatus.choices,
        default=CandidateStatus.INVITED
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class CandidateToken(models.Model):
    candidate = models.OneToOneField(Candidate, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=3)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
