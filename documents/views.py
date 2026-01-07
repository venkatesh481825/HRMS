from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.template.loader import render_to_string
from django.views.decorators.csrf import ensure_csrf_cookie
from candidate.models import Candidate
from .models import Document, DocumentStatus, DocumentToken
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from accounts.models import UserRole, UserProfile
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Q
from datetime import datetime

@ensure_csrf_cookie
def upload_document(request, token):
    try:
        token_obj = DocumentToken.objects.get(token=token)
    except DocumentToken.DoesNotExist:
        return render(request, "candidate/error.html", {
            "error_title": "Invalid Link",
            "error_message": "The document upload link you're trying to access is invalid. Please contact HR for a new link."
        })

    if not token_obj.is_valid():
        return render(request, "candidate/error.html", {
            "error_title": "Link Expired or Already Used",
            "error_message": "This document upload link has expired or has already been used. Please contact HR for a new link."
        })

    candidate = token_obj.candidate

    if request.method == "POST":
        document_type = request.POST.get("document_type")
        file = request.FILES.get("file")

        if document_type and file:
            Document.objects.create(
                candidate=candidate,
                document_type=document_type,
                file=file
            )
            messages.success(request, f"{document_type} uploaded successfully!")
            # Redirect to prevent form resubmission
            return redirect('upload_document', token=token)
        else:
            messages.error(request, "Please fill all fields.")

    # Get all documents for this candidate
    documents = Document.objects.filter(candidate=candidate).order_by('-uploaded_at')
    
    return render(request, "documents/upload.html", {
        "candidate": candidate,
        "documents": documents,
        "token": token
    })


@login_required
def hr_dashboard(request):
    """HR Dashboard to view and verify documents"""
    if request.user.userprofile.role != UserRole.HR:
        return HttpResponse("Not allowed. HR access only.")
    
    # Get all candidates with documents
    candidates_with_docs = Candidate.objects.filter(
        document__isnull=False
    ).distinct().annotate(
        total_docs=Count('document'),
        pending_docs=Count('document', filter=Q(document__status=DocumentStatus.PENDING)),
        verified_docs=Count('document', filter=Q(document__status=DocumentStatus.VERIFIED))
    ).order_by('-created_at')
    
    # Get all pending documents
    pending_documents = Document.objects.filter(status=DocumentStatus.PENDING).order_by('-uploaded_at')
    
    # Get all documents grouped by candidate
    all_documents = Document.objects.all().order_by('-uploaded_at')
    
    # Check which candidates have all documents verified and don't have user accounts yet
    candidates_ready_for_credentials = []
    candidates_with_accounts = {}  # Store username for candidates who have accounts
    for candidate in candidates_with_docs:
        if candidate.pending_docs == 0 and candidate.verified_docs > 0:
            user = User.objects.filter(email=candidate.email).first()
            if not user:
                candidates_ready_for_credentials.append(candidate.id)
            else:
                # Store username for display
                candidates_with_accounts[candidate.id] = user.username
    
    context = {
        'candidates': candidates_with_docs,
        'pending_documents': pending_documents,
        'all_documents': all_documents,
        'candidates_ready_for_credentials': candidates_ready_for_credentials,
        'candidates_with_accounts': candidates_with_accounts,
    }
    
    return render(request, "documents/hr_dashboard.html", context)


@login_required
def verify_document(request, doc_id):
    if request.user.userprofile.role != UserRole.HR:
        return HttpResponse("Not allowed")

    try:
        document = Document.objects.get(id=doc_id)
    except Document.DoesNotExist:
        messages.error(request, "Document not found")
        return redirect('hr_dashboard')

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "verify":
            document.status = DocumentStatus.VERIFIED
            document.save()
            messages.success(request, "Document verified successfully!")
            
        elif action == "reupload":
            document.status = DocumentStatus.REUPLOAD
            document.save()
            messages.info(request, "Document marked for re-upload.")

        return redirect('hr_dashboard')

    return render(request, "documents/verify.html", {"document": document})


@login_required
def send_login_credentials(request, candidate_id):
    """HR manually sends login credentials to candidate after all documents are verified"""
    # Only allow POST requests for security
    if request.method != 'POST':
        messages.error(request, "Invalid request method. Please use the form.")
        return redirect('hr_dashboard')
    
    if request.user.userprofile.role != UserRole.HR:
        return HttpResponse("Not allowed")

    try:
        candidate = Candidate.objects.get(id=candidate_id)
    except Candidate.DoesNotExist:
        messages.error(request, "Candidate not found")
        return redirect('hr_dashboard')

    # Check if all documents are verified
    all_documents = Document.objects.filter(candidate=candidate)
    if not all_documents.exists():
        messages.error(request, "No documents found for this candidate.")
        return redirect('hr_dashboard')
    
    all_verified = all(
        doc.status == DocumentStatus.VERIFIED for doc in all_documents
    )
    
    if not all_verified:
        messages.warning(request, "Not all documents are verified. Please verify all documents first.")
        return redirect('hr_dashboard')
    
    # Generate username from candidate name (lowercase, remove spaces)
    if candidate.name:
        # Convert name to lowercase and remove spaces
        username = candidate.name.lower().replace(' ', '').strip()
    else:
        # Fallback to email if name is not available
        username = candidate.email.split('@')[0]
    
    # Generate password: First letter uppercase of name + @ + current year
    current_year = datetime.now().year
    if candidate.name:
        # Capitalize first letter of name for password
        password_name = candidate.name.strip().split()[0]  # Take first word if multiple words
        password = f"{password_name.capitalize()}@{current_year}"
    else:
        # Fallback if name is not available
        password = f"{username.capitalize()}@{current_year}"
    
    # Check if user already exists - if yes, reset password and resend
    user = User.objects.filter(email=candidate.email).first()
    if user:
        # User exists - reset password and resend credentials
        user.set_password(password)
        user.save()
        # Update user profile if it exists, otherwise create it
        # Use get_or_create to safely handle existing profiles
        try:
            user_profile = UserProfile.objects.get(user=user)
            # Profile exists, update role
            user_profile.role = UserRole.EMPLOYEE
            user_profile.save()
        except UserProfile.DoesNotExist:
            # Profile doesn't exist, create it
            UserProfile.objects.create(user=user, role=UserRole.EMPLOYEE)
        messages.info(request, f"Password reset and credentials will be resent to {candidate.email}")
    else:
        # Create new user account
        # Note: The signal will automatically create UserProfile with HR role
        # So we need to update it after creation, not create a new one
        user = User.objects.create_user(
            username=username,
            email=candidate.email,
            password=password,
            first_name=candidate.name.split()[0] if candidate.name else '',
            last_name=' '.join(candidate.name.split()[1:]) if candidate.name and len(candidate.name.split()) > 1 else ''
        )
        
        # Signal creates UserProfile automatically, so just update the role
        # Wait a moment for signal to complete, then update
        try:
            user_profile = UserProfile.objects.get(user=user)
            # Profile was created by signal, update role to EMPLOYEE
            user_profile.role = UserRole.EMPLOYEE
            user_profile.save()
        except UserProfile.DoesNotExist:
            # Signal didn't fire (shouldn't happen), create profile
            UserProfile.objects.create(user=user, role=UserRole.EMPLOYEE)
    
    # Send login credentials email
    login_url = f"http://127.0.0.1:8000/accounts/login/"
    # BASE_URL = "https://abcd-1234.ngrok-free.app"
    # login_url = f"{BASE_URL}/accounts/login/"
    
    subject = "Your HRMS Login Credentials"
    
    message = f"""
Hello {candidate.name},

Congratulations! All your documents have been verified.

Your HRMS account has been created. You can now login using the following credentials:

Username: {username}
Password: {password}

Login URL: {login_url}

Please change your password after first login for security.

Regards,
HR Team
"""
    
    html_message = render_to_string(
        'documents/email_login_credentials.html',
        {
            'candidate_name': candidate.name,
            'username': username,
            'password': password,
            'login_url': login_url,
        }
    )
    
    # Debug information
    print("=" * 50)
    print("ATTEMPTING TO SEND EMAIL")
    print(f"To: {candidate.email}")
    print(f"From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Subject: {subject}")
    print(f"SMTP Host: {settings.EMAIL_HOST}")
    print(f"SMTP Port: {settings.EMAIL_PORT}")
    print(f"Use TLS: {settings.EMAIL_USE_TLS}")
    print("=" * 50)
    
    try:
        result = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [candidate.email],
            fail_silently=False,
            html_message=html_message,
        )
        print(f"Send mail result: {result}")
        if result:
            messages.success(request, f"✅ Login credentials sent successfully to {candidate.email}")
            print(f"✅ Email sent successfully to {candidate.email}")
        else:
            messages.error(request, f"Email sending returned False. Check email configuration.")
            print(f"❌ Email sending failed - returned False for {candidate.email}")
    except Exception as e:
        error_msg = str(e)
        messages.error(request, f"Failed to send email: {error_msg}")
        print(f"❌ Email error: {error_msg}")
        print(f"Attempted to send to: {candidate.email}")
        print(f"From: {settings.DEFAULT_FROM_EMAIL}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
    
    return redirect('hr_dashboard')
