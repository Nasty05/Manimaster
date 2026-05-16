from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):  # Моделька пользователя
    class Role(models.TextChoices):
        CLIENT = 'client', 'Клиент'
        MASTER = 'master', 'Мастер'
        ADMIN = 'admin', 'Администратор'

    username_validator = ASCIIUsernameValidator()
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=256,
        unique=True,
        validators=[username_validator],
    )
    name = models.CharField(
        verbose_name='Имя',
        max_length=150,
        validators=[
            RegexValidator(
                regex='^[А-Яа-яЁё]+$',
                message='Используйте толкьо русские символы.'
            )
        ],
        null=True,
    )
    surname = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
        validators=[
            RegexValidator(
                regex='^[А-Яа-яЁё]+$',
                message='Используйте толкьо русские символы.'
            )
        ],
        null=True,
    )
    email = models.EmailField(
        verbose_name='E-mail'
    )
    phone_number = models.CharField(
        verbose_name='Номер телефона',
        max_length=15,
        null=True,
    )
    role = models.CharField(
        verbose_name='Роль',
        max_length=10,
        choices=Role.choices,
        default=Role.CLIENT,
        help_text='Определяет права доступа в системе'
    )
    last_activity = models.DateTimeField(
        verbose_name='Последняя активность',
        auto_now=True
    )

    def __str__(self):  # для отображения в админке и консоли
        return f"{self.username} ({self.get_role_display()})"  # Показывает логин и роль

    # Проверки по ролям
    def is_master(self):
        return self.role == self.Role.MASTER or self.is_superuser

    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_client(self):
        return self.role == self.Role.CLIENT and not self.is_superuser

    def get_full_name(self):  # Возвращает полное имя или логин
        if self.name and self.surname:
            return f"{self.surname} {self.name}"
        return self.username

    # проверка на разрешение зайти на определенные страницы
    def can_access_master_panel(self):
        return self.is_master() or self.is_admin_user() or self.is_superuser and not self.is_client()

    def can_access_admin_panel(self):
        return self.is_admin_user() or self.is_superuser and not self.is_client() and not self.is_master()

    # Метод сохранения
    def save(self, *args, **kwargs):
        # Автоматически даем доступ к админке для администраторов
        if self.role == self.Role.ADMIN or self.is_superuser:
            self.is_staff = True
        else:
            self.is_staff = False
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        db_table = 'user'  # имя в базе данных
        indexes = [
            models.Index(fields=['role']),  # для быстрого поиска роли
            models.Index(fields=['-last_activity']),  # индекс сортировки по убыванию активности
        ]
