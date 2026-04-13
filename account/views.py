from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from account.forms import OnboardingForm
from django.contrib import messages
from .models import EmailVerificationCode


@login_required
def complete_profile(request):
    if request.method == 'POST':
        form = OnboardingForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = OnboardingForm(instance=request.user)
    return render(request, 'account/complete_profile.html', {'form': form})


from allauth.account.models import EmailAddress

from django.contrib.auth import login
from .models import EmailVerificationCode
from allauth.account.models import EmailAddress


def verify_code_view(request):
    if request.method == 'POST':
        input_code = request.POST.get('code')
        try:
            verification = EmailVerificationCode.objects.get(code=input_code)

            if verification.is_valid():
                user = verification.user

                email_obj, created = EmailAddress.objects.get_or_create(
                    user=user,
                    email=user.email
                )
                email_obj.verified = True
                email_obj.save()

                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                verification.delete()

                messages.success(request, "Почта подтверждена, добро пожаловать!")
                return redirect('/')
            else:
                messages.error(request, "Код просрочен.")

        except EmailVerificationCode.DoesNotExist:
            messages.error(request, "Неверный код подтверждения.")

    return render(request, 'account/email_confirm.html')