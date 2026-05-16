from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import User

# Кастомные формы для админки

class CustomUserChangeForm(UserChangeForm): # Форма редактирования пользователей
    class Meta(UserChangeForm.Meta):
        model = User # используеться кастомная модель
        fields = '__all__' # показывает все поля модели


class CustomUserCreationForm(UserCreationForm): # форма создания нового пользователя
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'name', 'surname', 'phone_number', 'role') # Отображаемые поля

# Настройка отобраения модельки юзер в админке

class UserAdmin(BaseUserAdmin): # для модельки юзер
    # Используемые формы
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ('username', 'email', 'name', 'surname', 'role', 'is_staff', 'is_active') # отображаемые поля
    list_filter = ('role', 'is_staff', 'is_active', 'is_superuser') # фильтры сбоку

    fieldsets = ( # Группировка полей
        (None, {'fields': ('username', 'password')}),
        (_('Персональные данные'), {'fields': ('name', 'surname', 'email', 'phone_number')}),
        (_('Права доступа'),
         {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Важные даты'), {'fields': ('last_login', 'date_joined')}),  # last_activity удалён
    )

    add_fieldsets = ( # Настраивает поля
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'name', 'surname', 'phone_number', 'role', 'password1', 'password2'),
        }),
    )

    search_fields = ('username', 'email', 'name', 'surname') # для поиска
    ordering = ('username',) # сортировка по логину
    filter_horizontal = ('groups', 'user_permissions') # для полей многих ко многим

admin.site.register(User, UserAdmin) # Регистрирует модельку