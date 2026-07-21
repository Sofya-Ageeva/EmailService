from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .forms import UserRegistrationForm, UserLoginForm
from .models import User


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()

            # Отправка приветственного письма
            try:
                send_mail(
                    subject='Добро пожаловать в EmailService!',
                    message=f'Приветствуем вас, {user.email}!\n\n'
                            f'Вы успешно зарегистрировались в сервисе управления рассылками.\n'
                            f'Теперь вы можете создавать рассылки и управлять клиентами.\n\n'
                            f'С уважением,\nКоманда EmailService',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f'Ошибка отправки письма: {e}')

            messages.success(request, f'Аккаунт {user.email} успешно создан!')
            return redirect('users:login')
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.email}!')
                return redirect('newsletter:home')
        else:
            messages.error(request, 'Неверный email или пароль.')
    else:
        form = UserLoginForm()

    return render(request, 'users/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('newsletter:home')


@login_required
def profile(request):
    return render(request, 'users/profile.html', {'user': request.user})
