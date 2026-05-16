# fix_superuser_roles.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project1.settings')
django.setup()

from authapp.models import User


def fix_superuser_roles():
    """Назначает правильные роли для superuser"""

    print("Исправление ролей superuser...")

    # Находим всех superuser
    superusers = User.objects.filter(is_superuser=True)

    for user in superusers:
        old_role = user.role
        user.role = User.Role.ADMIN  # Назначаем роль ADMIN
        user.save()
        print(f"Пользователь {user.username}: {old_role} -> {user.role} (ADMIN)")

    print(f"Исправлено {superusers.count()} superuser'ов")


if __name__ == '__main__':
    fix_superuser_roles()