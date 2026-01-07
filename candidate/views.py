from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import render_to_string
from accounts.models import UserRole
from .models import Candidate, CandidateToken, CandidateStatus
from documents.models import DocumentToken
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
# HR creates candidate & gets link
@login_required
def create_candidate(request):
    # Check if user has HR role or is superuser
    if request.user.is_superuser:
        # Superuser can access
        pass
    elif not hasattr(request.user, 'userprofile'):
        # Create userprofile if it doesn't exist
        from accounts.models import UserProfile
        UserProfile.objects.create(user=request.user, role=UserRole.HR)
    elif request.user.userprofile.role != UserRole.HR:
        return render(request, "candidate/error.html", {
            "error_title": "Access Denied",
            "error_message": "You need HR role to create candidates. Please contact administrator."
        })

    if request.method == "POST":
        email = request.POST.get("email")

        #  1. Check if candidate already exists
        candidate, created = Candidate.objects.get_or_create(
            email=email
        )

        #  2. If candidate already invited, reset status if needed
        if not created and candidate.status == "PROFILE_COMPLETED":
            messages.error(request, "Candidate already completed onboarding.")
            return render(request, "candidate/create_candidate.html")

        #  3. Delete old token if exists
        CandidateToken.objects.filter(candidate=candidate).delete()

        #  4. Create fresh token
        token = CandidateToken.objects.create(candidate=candidate)

        link = f"http://127.0.0.1:8000/candidate/onboard/{token.token}/"
        # BASE_URL = "https://abcd-1234.ngrok-free.app"
        # link = f"{BASE_URL}/candidate/onboard/{token.token}/"

        subject = "Complete Your Onboarding"
        
        # Plain text message (fallback for email clients that don't support HTML)
        message = f"""
Hello,

You have been invited to complete your onboarding process.

Click the link below:
{link}

Note: This link will expire in 3 days.

Regards,
HR Team
"""

        # HTML email template
        html_message = render_to_string(
            'candidate/email_onboarding.html',
            {
                'onboarding_link': link,
            }
        )

        try:
            result = send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
                html_message=html_message,
            )
            if result:
                messages.success(request, f"Onboarding link sent successfully to {email}!")
                print(f"Email sent successfully to {email}")
            else:
                messages.error(request, f"Email sending returned False. Check email configuration.")
                print(f"Email sending failed - returned False for {email}")
        except Exception as e:
            error_msg = str(e)
            messages.error(request, f"Failed to send email: {error_msg}")
            print(f"Email error: {error_msg}")
            print(f"Attempted to send to: {email}")
            print(f"From: {settings.DEFAULT_FROM_EMAIL}")
            import traceback
            traceback.print_exc()

        return render(request, "candidate/create_candidate.html")

    return render(request, "candidate/create_candidate.html")


# Candidate opens link (NO LOGIN)
def candidate_onboard(request, token):
    try:
        token_obj = CandidateToken.objects.get(token=token)
    except CandidateToken.DoesNotExist:
        return render(request, "candidate/error.html", {
            "error_title": "Invalid Link",
            "error_message": "The onboarding link you're trying to access is invalid. Please contact HR for a new link."
        })

    if not token_obj.is_valid():
        return render(request, "candidate/error.html", {
            "error_title": "Link Expired or Already Used",
            "error_message": "This onboarding link has expired or has already been used. Please contact HR for a new link."
        })

    candidate = token_obj.candidate

    if request.method == "POST":
        candidate.name = request.POST.get("name")
        candidate.phone = request.POST.get("phone")
        candidate.status = CandidateStatus.PROFILE_COMPLETED
        candidate.save()

        token_obj.is_used = True
        token_obj.save()

        # Create document upload token and redirect directly to upload page
        DocumentToken.objects.filter(candidate=candidate).delete()
        doc_token = DocumentToken.objects.create(candidate=candidate)
        
        # Redirect directly to document upload page with success message
        messages.success(request, f"Profile completed successfully! Please upload your documents below.")
        return redirect('upload_document', token=doc_token.token)

    return render(request, "candidate/onboard_form.html")
