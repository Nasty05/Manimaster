from django.db import migrations


def set_staff_for_admins(apps, schema_editor):
    User = apps.get_model('authapp', 'User')
    # Даем is_staff=True всем админам и суперпользователям
    User.objects.filter(role='admin').update(is_staff=True)
    User.objects.filter(is_superuser=True).update(is_staff=True)
    # Убираем is_staff у обычных пользователей
    User.objects.filter(role='client').exclude(is_superuser=True).update(is_staff=False)
    User.objects.filter(role='master').exclude(is_superuser=True).update(is_staff=False)


class Migration(migrations.Migration):
    dependencies = [
        ('authapp', '0002_user_last_activity_user_role_and_more'),
    ]

    operations = [
        migrations.RunPython(set_staff_for_admins),
    ]
