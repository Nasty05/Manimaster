# импорты
from datetime import datetime, timedelta # дата и время
from django.contrib import messages # всплывающие сообщения
from django.contrib.auth.decorators import login_required # декоратор доступ авторизованным пользователям
from django.db import models # для сложных ORM запросов
from django.http import JsonResponse # для JSON
from django.shortcuts import render, get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localdate
from django.views.decorators.http import require_http_methods, require_POST, require_GET
# импорты из других приложений
from authapp.models import User
from .forms import CustomUserChangeForm, AssignRoleForm
from .forms import ReviewForm
from .models import Service, PortfolioItem, Review, Booking, MasterException, MasterSchedule, \
    WeeklyTimeOff
from .services import ScheduleService


def is_admin(user): # проверка на админа
    return user.is_authenticated and (user.is_admin_user() or user.is_superuser)


def is_master_or_admin(user): # поверка на мастера или админа
    return user.is_authenticated and (user.is_master() or user.is_admin_user() or user.is_superuser)

# отзывы
@login_required
def add_review_view(request, booking_id): # контроллер чтоб отзыв был только к завершённой записи и только у авторизованных
    booking = get_object_or_404(Booking, id=booking_id, user=request.user) # находим запись данного пользователя

    if hasattr(booking, 'review'): # проверяем есть ли отзыв у данной записи
        messages.error(request, 'Вы уже оставили отзыв на эту запись')
        return redirect('mainapp:profile')

    from datetime import date
    if booking.date > date.today(): # нельзя оставить отзыв на будующие услуги
        messages.error(request, 'Нельзя оставить отзыв до оказания услуги')
        return redirect('mainapp:profile')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid(): # создаем отзыв без сохранения в базу данных
            review = form.save(commit=False)
            review.booking = booking
            review.user = request.user
            review.service = booking.service
            review.save() # сохраняем в базу данных

            messages.success(request, 'Спасибо за ваш отзыв!')
            return redirect('mainapp:profile')
    else:
        form = ReviewForm()

    return render(request, 'mainapp/add_review.html', {
        'form': form,
        'booking': booking
    })

# AJAX методы для формы записи
def get_masters_for_service(request, service_id): # возвращает мастеров которые выполняют услугу эту
    try:
        service = Service.objects.get(id=service_id)
        masters = service.masters.filter(role='master').values('id', 'name', 'surname') # берем только пользователей с ролью мастер

        masters_list = []
        for master in masters:
            masters_list.append({
                'id': master['id'],
                'name': f"{master['surname']} {master['name']}" if master['name'] and master['surname'] else "Мастер" # формируем фио либо остается подпись мастер
            })

        return JsonResponse({
            'masters': masters_list
        })
    except Service.DoesNotExist:
        return JsonResponse({'masters': []})


@require_GET
def get_available_slots(request): # возвращает свободное время и даты на услугу по мастеру
    try:
        master_id = request.GET.get('master_id')
        service_id = request.GET.get('service_id')
        date_str = request.GET.get('date')

        print(f"get_available_slots вызван: master={master_id}, service={service_id}, date={date_str}")

        # проверка наличия всех параметров
        if not all([master_id, service_id, date_str]):
            return JsonResponse({'error': 'Не все параметры переданы'}, status=400)

        # преобразуем строку даты в обьект date
        from datetime import datetime
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Неверный формат даты'}, status=400)

        # получаем свободные слоты услуг
        slots = ScheduleService.get_available_slots(master_id, service_id, date)

        # преобразуем обьект time в строку по типу 00:00
        slots_str = [slot.strftime('%H:%M') for slot in slots]

        return JsonResponse({
            'slots': slots_str,
            'date': date_str,
            'master_id': master_id,
            'service_id': service_id,
            'count': len(slots_str)
        })
    except Exception as e:
        print(f"Ошибка в get_available_slots: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


# основные страницы
def index(request): # показывает 6 последних отзывов на странице со средними оценками
    reviews = Review.objects.filter(is_public=True).select_related('user', 'service').order_by('-created_at')[:6] # связанные модели юзер и сервис

    for review in reviews: # расчет средней оценки для каждого отзыва
        review.avg_rating = round((
            review.speed_rating +
            review.quality_rating +
            review.design_rating +
            review.cleanliness_rating +
            review.price_rating
        ) / 5, 1)

    context = {
        'reviews': reviews,
        'title': 'Главная',
    }
    return TemplateResponse(request, 'mainapp/index.html', context)


def portfolio_view(request): # Партфолио. выводит все работы в порядке убывания даты
    items = PortfolioItem.objects.all().order_by('-date_created')
    context = {
        'items': items,
    }
    return render(request, 'mainapp/portfolio.html', context)


@require_http_methods(["GET", "POST"])
def services_view(request):  # страница услуг и форма записи
    if request.method == "POST": # получает данные из формы
        service_id = request.POST.get('service')
        master_id = request.POST.get('master')
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        date = request.POST.get('date')
        time = request.POST.get('time')

        errors = []

        # валидация обязательных полей
        if not service_id:
            errors.append("Услуга не выбрана.")
        if not master_id:
            errors.append("Выберите мастера.")
        if not name:
            errors.append("Введите имя.")
        if not phone:
            errors.append("Введите телефон.")
        if not date:
            errors.append("Введите дату.")
        if not time:
            errors.append("Введите время.")

        today = localdate() #дата сегодня
        date_obj = None
        time_obj = None

        # валидация даты и проверка на прошлость даты
        if date and not errors:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                if date_obj < today:
                    errors.append("Дата не может быть в прошлом.")
            except ValueError:
                errors.append("Неверный формат даты.")

        # валидация времени
        if time and not errors:
            try:
                time_obj = datetime.strptime(time, '%H:%M').time()
            except ValueError:
                errors.append("Неверный формат времени.")

        # если ошибка то сообщение
        if errors:
            services = Service.objects.all()
            return render(request, 'mainapp/services.html', {
                'services': services,
                'errors': errors,
                'today': today.isoformat(),
                'form_data': {  # сохранение данных для автозаполенения
                    'service': service_id,
                    'master': master_id,
                    'name': name,
                    'phone': phone,
                    'date': date,
                    'time': time
                }
            })

        # проверка существования услуги
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            errors.append("Выбранная услуга не найдена.")
            services = Service.objects.all()
            return render(request, 'mainapp/services.html', {
                'services': services,
                'errors': errors,
                'today': today.isoformat()
            })

        # проверка мастера на существо и выполениение услуги
        from authapp.models import User
        try:
            master = User.objects.get(id=master_id, role='master')
            if not service.masters.filter(id=master_id).exists():
                errors.append("Выбранный мастер не выполняет эту услугу.")
        except User.DoesNotExist:
            errors.append("Выбранный мастер не найден.")

        # проверка времени выбранного
        if not errors and date_obj and time_obj:
            from .services import ScheduleService
            if not ScheduleService.is_slot_available(master_id, service_id, date_obj, time_obj):
                errors.append("Выбранное время уже занято. Пожалуйста, выберите другое время.")

        # если ошибка возвращаем форму
        if errors:
            services = Service.objects.all()
            return render(request, 'mainapp/services.html', {
                'services': services,
                'errors': errors,
                'today': today.isoformat(),
                'form_data': {
                    'service': service_id,
                    'master': master_id,
                    'name': name,
                    'phone': phone,
                    'date': date,
                    'time': time
                }
            })

        # все ок? создаем запись
        booking = Booking.objects.create(
            service=service,
            master=master,
            name=name,
            phone=phone,
            date=date_obj,
            time=time_obj
        )

        # если пользователь авторизован то запись в профиль
        if request.user.is_authenticated:
            booking.user = request.user
            booking.save()

        # обрато к услугам и сообщение что записали
        return redirect(f"{reverse('mainapp:services')}?success=1")

    # страница услуг
    services = Service.objects.all()
    today = localdate().isoformat()
    max_date = (datetime.strptime(today, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
    success = request.GET.get('success') == '1'

    return render(request, 'mainapp/services.html', {
        'services': services,
        'today': today,
        'max_date': max_date,
        'success': success,
    })


# ПРОФИЛЬ.
@login_required
def profile_view(request): # показывает записи

    user_bookings = Booking.objects.filter(user=request.user).order_by('-date', '-time') # сортировка по дате

    from datetime import date
    today = date.today()

    upcoming_bookings = user_bookings.filter(date__gte=today).order_by('date', 'time') # предстоящие
    past_bookings = user_bookings.filter(date__lt=today).order_by('-date', '-time') # прошедшие

    context = {
        'user': request.user,
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'bookings_count': user_bookings.count(),
    }
    return render(request, 'mainapp/profile.html', context)



@login_required
def edit_profile_view(request):  #  редактирование профиля (пароль отдельно тут все по модельке)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('mainapp:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)

    return render(request, 'mainapp/edit_profile.html', {'form': form})


@login_required
def change_password_view(request): #  смена пароля чтоб без перезахода в аккаунт
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) #  обновляем сессию
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('mainapp:profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'mainapp/change_password.html', {'form': form})


#  ОТМЕНА ЗАПИСИ
@login_required
@require_POST
def cancel_booking_view(request, booking_id): # чтоб нельзя было отменить уже сделанную запись и меньше чем за 2 часа до начала. при отмене удалялась.
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    from datetime import date, datetime, timedelta
    if booking.date < date.today(): #  проверка на прошлое
        messages.error(request, 'Нельзя отменить прошедшую запись')
        return redirect('mainapp:profile')

    booking_datetime = datetime.combine(booking.date, booking.time) # проверка на 2 часа до записи
    if booking_datetime - datetime.now() < timedelta(hours=2):
        messages.error(request, 'Запись можно отменить минимум за 2 часа')
        return redirect('mainapp:profile')

    service_title = booking.service.title
    booking_date = booking.date
    booking.delete() # удаляем

    messages.success(request, f'Запись на услугу "{service_title}" на {booking_date} успешно отменена') #  сообщение
    return redirect('mainapp:profile')


#  ПАНЕЛЬ МАСТЕРА
@login_required
def master_panel_view(request): # панелька управления для мастера. статистика
    if not is_master_or_admin(request.user): #  проверка на права
        messages.error(request, 'У вас нет доступа к этой странице.')
        return redirect('mainapp:profile')

    master = request.user
    today = timezone.now().date()

    #  расчет отценки мастера по отзывам по 5 критериям
    reviews = Review.objects.filter(booking__master=master)
    if reviews.exists():
        total_avg = sum(review.average_rating() for review in reviews)
        avg_rating = round(total_avg / reviews.count(), 1)
    else:
        avg_rating = 0

    stats = { #  статистика
        'today': Booking.objects.filter( #  сегодяшние записи
            master=master,
            date=today,
            status__in=['pending', 'confirmed']
        ).count(),

        'pending': Booking.objects.filter( # ждущие подтверждения
            master=master,
            status='pending',
            date__gte=today
        ).count(),

        'total_completed': Booking.objects.filter( # выполненные
            master=master,
            status='completed'
        ).count(),
        'avg_rating': avg_rating,
    }

    today_bookings = Booking.objects.filter( # сегодняшние записи детально
        master=master,
        date=today
    ).select_related('service', 'user').order_by('time')

    working_hours = None # рабочие часы на сегодня (база нет)
    try: # исключение на дату ищет
        exception = MasterException.objects.get(master=master, date=today)
        if exception.is_working:
            working_hours = {
                'start': exception.start_time,
                'end': exception.end_time,
                'is_working': True,
                'is_exception': True
            }
        else:
            working_hours = {'is_working': False}
    except MasterException.DoesNotExist:
        day_of_week = today.isoweekday() # нет исключений значит регулярное распиание
        try:
            schedule = MasterSchedule.objects.get(
                master=master,
                day_of_week=day_of_week,
                is_active=True
            )
            working_hours = {
                'start': schedule.start_time,
                'end': schedule.end_time,
                'is_working': True,
                'slot_duration': schedule.slot_duration
            }
        except MasterSchedule.DoesNotExist:
            working_hours = {'is_working': False}

    weekly_time_offs = WeeklyTimeOff.objects.filter( # перерывы
        master=master,
        is_active=True
    ).order_by('day_of_week', 'start_time')

    # данные для графика 30 дней
    end_date = today
    start_date = end_date - timedelta(days=30)
    chart_data = []
    chart_labels = []

    current_date = start_date
    while current_date <= end_date: # количсетво записей на день готовых и подтвержденных
        bookings_count = Booking.objects.filter(
            master=master,
            date=current_date,
            status__in=['completed', 'confirmed']
        ).count()
        chart_labels.append(current_date.strftime('%d.%m'))
        chart_data.append(bookings_count)
        current_date += timedelta(days=1)

    context = {
        'user': master,
        'stats': stats,
        'today_bookings': today_bookings,
        'working_hours': working_hours,
        'weekly_time_offs': weekly_time_offs,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'mainapp/master_panel.html', context)


#  АДМИНКА
@login_required
def admin_panel_view(request): # панель админа
    if not is_admin(request.user): # если не админ
        messages.error(request, 'У вас нет доступа к этой странице.') # сообщение
        return redirect('mainapp:profile')

    users = User.objects.exclude(is_superuser=True).order_by('-date_joined') # все кроме суперюзеров
    # статистика
    total_users = users.count()
    total_clients = users.filter(role=User.Role.CLIENT, is_superuser=False).count()
    total_masters = users.filter(role=User.Role.MASTER, is_superuser=False).count()
    total_admins = users.filter(role=User.Role.ADMIN, is_superuser=False).count() + User.objects.filter(
        is_superuser=True).count()

    role_filter = request.GET.get('role', '') # фильтруем по ролям
    if role_filter:
        users = users.filter(role=role_filter)

    search_query = request.GET.get('search', '') # поиск по данным
    if search_query:
        users = users.filter(
            models.Q(username__icontains=search_query) |
            models.Q(name__icontains=search_query) |
            models.Q(surname__icontains=search_query) |
            models.Q(email__icontains=search_query)
        )

    context = {
        'users': users,
        'role_choices': User.Role.choices,
        'current_filter': role_filter,
        'search_query': search_query,
        'stats': {
            'total': total_users,
            'clients': total_clients,
            'masters': total_masters,
            'admins': total_admins,
        }
    }
    return render(request, 'mainapp/admin_panel.html', context)


@login_required
def change_user_role_view(request, user_id): # изменяет роль пользователей кроме своей
    if not is_admin(request.user): # если не админ
        messages.error(request, 'У вас нет прав для этого действия.') # сообщение
        return redirect('mainapp:profile')

    user = get_object_or_404(User, id=user_id)

    if user.is_superuser:
        messages.warning(request, 'Нельзя изменить роль суперпользователя.')
        return redirect('mainapp:admin_panel')

    if user == request.user:
        messages.warning(request, 'Вы не можете изменить свою собственную роль.')
        return redirect('mainapp:admin_panel')

    if request.method == 'POST':
        form = AssignRoleForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Роль пользователя {user.get_full_name()} изменена на {user.get_role_display()}'
            )
            return redirect('mainapp:admin_panel')
    else:
        form = AssignRoleForm(instance=user)

    return render(request, 'mainapp/change_role.html', {
        'form': form,
        'target_user': user
    })


#  расписание мастера
@login_required
def master_schedule_view(request): # добавляем редактируем расписания. исключения и перерывы
    if not is_master_or_admin(request.user):
        messages.error(request, 'У вас нет доступа к этой странице.')
        return redirect('mainapp:profile')

    from .models import MasterSchedule, MasterException, WeeklyTimeOff
    from datetime import date

    master = request.user
    today = date.today()

    regular_schedule = MasterSchedule.objects.filter( # регулярное расписание
        master=master,
        is_active=True
    ).order_by('day_of_week')

    weekly_time_offs = WeeklyTimeOff.objects.filter( # регулярные перерывы
        master=master,
        is_active=True
    ).order_by('day_of_week', 'start_time')

    exceptions = MasterException.objects.filter( # исключения
        master=master,
        date__gte=today
    ).order_by('date')[:20]

    if request.method == 'POST': # для удаления и добавления
        action = request.POST.get('action')

        if action == 'add_schedule':
            day = request.POST.get('day_of_week')
            start = request.POST.get('start_time')
            end = request.POST.get('end_time')
            duration = request.POST.get('slot_duration', 60)

            MasterSchedule.objects.update_or_create(
                master=master,
                day_of_week=day,
                defaults={
                    'start_time': start,
                    'end_time': end,
                    'slot_duration': duration,
                    'is_active': True
                }
            )
            messages.success(request, 'Расписание добавлено')

        elif action == 'delete_schedule':
            schedule_id = request.POST.get('schedule_id')
            MasterSchedule.objects.filter(id=schedule_id, master=master).delete()
            messages.success(request, 'Расписание удалено')

        elif action == 'add_weekly_timeoff':
            day = request.POST.get('day_of_week')
            start = request.POST.get('start_time')
            end = request.POST.get('end_time')
            reason = request.POST.get('reason', 'Обед')

            WeeklyTimeOff.objects.create(
                master=master,
                day_of_week=day,
                start_time=start,
                end_time=end,
                reason=reason
            )
            messages.success(request, 'Регулярный перерыв добавлен')

        elif action == 'delete_weekly_timeoff':
            timeoff_id = request.POST.get('timeoff_id')
            WeeklyTimeOff.objects.filter(id=timeoff_id, master=master).delete()
            messages.success(request, 'Регулярный перерыв удален')

        elif action == 'add_exception':
            date = request.POST.get('date')
            exception_type = request.POST.get('exception_type')
            reason = request.POST.get('reason', '')
            if exception_type == 'not_working': # мастер не работает в данный день
                is_working = False
                start_time = None
                end_time = None
                break_start = None
                break_end = None
                break_reason = ''
            elif exception_type == 'different_time': # работает с исключениями
                is_working = True
                start_time = request.POST.get('start_time')
                end_time = request.POST.get('end_time')
                use_special_breaks = request.POST.get('use_special_breaks') == 'on'
                if use_special_breaks:
                    break_start = request.POST.get('break_start')
                    break_end = request.POST.get('break_end')
                    break_reason = request.POST.get('break_reason', '')
                else:
                    break_start = None
                    break_end = None
                    break_reason = ''
            else: # обычное распиание
                is_working = True
                start_time = None
                end_time = None
                break_start = None
                break_end = None
                break_reason = ''

            MasterException.objects.update_or_create(
                master=master,
                date=date,
                defaults={
                    'is_working': is_working,
                    'start_time': start_time,
                    'end_time': end_time,
                    'break_start': break_start,
                    'break_end': break_end,
                    'break_reason': break_reason,
                    'reason': reason
                }
            )
            messages.success(request, 'Исключение добавлено') # сообщение

        elif action == 'delete_exception':
            exception_id = request.POST.get('exception_id')
            MasterException.objects.filter(id=exception_id, master=master).delete()
            messages.success(request, 'Исключение удалено') # сообщение
        return redirect('mainapp:master_schedule')

    context = {
        'user': master,
        'regular_schedule': regular_schedule,
        'weekly_time_offs': weekly_time_offs,
        'exceptions': exceptions,
        'weekdays': MasterSchedule.DAYS_OF_WEEK,
        'today': today.isoformat(),
    }
    return render(request, 'mainapp/master_schedule.html', context)


#  измениение статуса для масетра
@login_required
def update_booking_status(request, booking_id):
    if not is_master_or_admin(request.user): # только мастеру чья запись
        messages.error(request, 'У вас нет доступа к этому действию.')
        return redirect('mainapp:profile')

    booking = get_object_or_404(Booking, id=booking_id, master=request.user)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['confirmed', 'completed', 'cancelled']:
            booking.status = new_status
            booking.save()
            messages.success(request, f'Статус записи изменен на {booking.get_status_display()}')

    return redirect('mainapp:master_panel')
