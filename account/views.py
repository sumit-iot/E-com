from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm
)

User = get_user_model()


def signup_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! Please sign in.')
            return redirect('account:signin')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'account/signup.html', {'form': form})


def signin_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'account/signin.html', {'form': form})


@login_required
def signout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been signed out successfully.')
    return redirect('account:signin')


def forgot_password_view(request):
    """Forgot password view - sends reset email"""
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                # Generate token for password reset
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Build reset URL
                current_site = get_current_site(request)
                reset_url = f"{settings.SITE_URL}/account/reset-password/{uid}/{token}/"
                
                # Create email message
                subject = 'Password Reset Request'
                message = render_to_string('account/password_reset_email.html', {
                    'user': user,
                    'reset_url': reset_url,
                    'site_name': current_site.name,
                })
                
                # Send email
                send_mail(
                    subject,
                    '',  # Plain text version (empty, using HTML only)
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    html_message=message,
                    fail_silently=False,
                )
                
                messages.success(
                    request,
                    'Password reset email has been sent. Please check your inbox.'
                )
                return redirect('account:signin')
            except User.DoesNotExist:
                # Don't reveal if email exists for security
                messages.success(
                    request,
                    'If an account exists with this email, a password reset link has been sent.'
                )
                return redirect('account:signin')
    else:
        form = CustomPasswordResetForm()
    
    return render(request, 'account/forgot_password.html', {'form': form})


def reset_password_view(request, uidb64, token):
    """Reset password view - handles password reset from email link"""
    if request.user.is_authenticated:
        return redirect('/')
    
    try:
        # Decode user ID
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    # Verify token
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been reset successfully. Please sign in with your new password.')
                return redirect('account:signin')
        else:
            form = CustomSetPasswordForm(user)
        
        return render(request, 'account/reset_password.html', {'form': form})
    else:
        messages.error(request, 'Invalid or expired password reset link. Please request a new one.')
        return redirect('account:forgot_password')
