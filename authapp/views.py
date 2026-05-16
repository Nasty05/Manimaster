from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from authapp.forms import LoginForm, CustomUserCreationForm  # импортируем новую форму


def login(request):  # Вход
    # Если форма отправлена
    if request.method == 'POST':
        form = LoginForm(data=request.POST)  # Создает форму с данными из запроса
        if form.is_valid():  # Валидность
            auth.login(request, form.get_user())  # Входит
            return HttpResponseRedirect(reverse('mainapp:index'))  # Перенаправляет на главную
    else:
        form = LoginForm()

    context = {
        'title': 'авторизация',
        'form': form,
    }
    return render(request, 'authapp/login.html', context)


def register(request):  # Регистрация
    if request.method == 'POST':  # Если форма отправлена
        form = CustomUserCreationForm(request.POST)  # используем новую форму
        if form.is_valid():  # Валидность
            user = form.save()  # Сохраняет нового пользователя
            messages.success(request, 'Регистрация прошла успешно! Теперь вы можете войти.')  # Сообщение
            return redirect('authapp:login')  # Перенаправляет на страницу входа
        else:
            # Добавляем сообщения об ошибках
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()

    context = {
        'title': 'регистрация',
        'form': form,
    }
    return render(request, 'authapp/register.html', context)


@login_required  # только дл авторизованных
def logout(request):  # выход из аккаунта
    auth.logout(request)  # перенаправляем на главную
    return HttpResponseRedirect(reverse('mainapp:index'))
