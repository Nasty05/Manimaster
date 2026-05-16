from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm

from authapp.models import User


class LoginForm(AuthenticationForm):  # Форма входа
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, item in self.fields.items():
            item.widget.attrs['class'] = 'form-control'


class CustomUserCreationForm(UserCreationForm):  # Кастомная форма регистрации
    # Доп поля
    name = forms.CharField(
        label='Имя',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Иван'})
    )
    surname = forms.CharField(
        label='Фамилия',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Иванов'})
    )
    email = forms.EmailField(
        label='E-mail',
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'example@mail.ru'})
    )
    phone_number = forms.CharField(
        label='Телефон',
        max_length=18,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '+7 (999) 123-45-67'})
    )

    class Meta:
        model = User
        fields = (
        'username', 'name', 'surname', 'email', 'phone_number', 'password1', 'password2')  # отображаються в форме

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'  # убирает стандартные подсказки
            field.help_text = ''

    def save(self, commit=True):  # сохранение
        user = super().save(commit=False)  # создает обьект но не сохраняет
        # Заполняет поля данных формы
        user.name = self.cleaned_data['name']
        user.surname = self.cleaned_data['surname']
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        user.role = User.Role.CLIENT  # базовая роль клиент
        if commit:
            user.save()  # сохраняет
        return user


class CustomUserChangeForm(UserChangeForm):  # Форма редактирования профиля

    def save(self, commit=True):
        user = super().save(commit=False)
        user.name = self.cleaned_data['name']
        user.surname = self.cleaned_data['surname']
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        user.role = User.Role.CLIENT  # всегда клиент

        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = ('username', 'name', 'surname', 'email', 'phone_number')


class AssignRoleForm(forms.ModelForm):  # Форма для назначения роли
    class Meta:
        model = User
        fields = ('role',)
        labels = {
            'role': 'Роль пользователя'
        }
