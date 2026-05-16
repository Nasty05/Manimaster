from datetime import datetime, timedelta

from django.utils import timezone


class ScheduleService: # для расписания мастеров

    @staticmethod
    def get_available_slots(master_id, service_id, date): # вернет список свободных времен для нужной мастера услуги и даты
        from authapp.models import User # импорт внутри чтоб не было циклических
        from .models import MasterSchedule, MasterException, Booking, Service, WeeklyTimeOff

        # Проверка что дата на месяц вперед
        today = timezone.now().date() # сегодня
        max_date = today + timedelta(days=30) # максимум 30 дне вперед

        if date > max_date: # если дата больше чем за месяц нельзя записаться
            return []

        try: # получит мастеров и услуги из базы данных
            master = User.objects.get(id=master_id, role='master')
            service = Service.objects.get(id=service_id)
        except (User.DoesNotExist, Service.DoesNotExist):
            return []

        # переменные для рабочих часов
        work_start = None
        work_end = None
        use_regular_breaks = True
        exception_obj = None
        special_breaks = []  # Список для специальных перерывов

        try: # Проверяем исключения для даты данной
            exception_obj = MasterException.objects.get(master=master, date=date)

            if not exception_obj.is_working: # не работает мастер
                return []

            if exception_obj.start_time and exception_obj.end_time: # исключения но работает
                work_start = exception_obj.start_time
                work_end = exception_obj.end_time
                use_regular_breaks = False

                if exception_obj.break_start and exception_obj.break_end: # специальные перерывы если есть
                    class BreakObj:
                        def __init__(self, start, end, reason):
                            self.start_time = start
                            self.end_time = end
                            self.reason = reason

                    special_breaks.append(BreakObj(
                        exception_obj.break_start,
                        exception_obj.break_end,
                        exception_obj.break_reason or 'Перерыв'
                    ))
            else: # в исключении нет измененного времени значит как обычно
                day_of_week = date.isoweekday()
                try:
                    schedule = MasterSchedule.objects.get(master=master, day_of_week=day_of_week, is_active=True)
                    work_start = schedule.start_time
                    work_end = schedule.end_time
                    use_regular_breaks = True
                except MasterSchedule.DoesNotExist:
                    return []

        except MasterException.DoesNotExist: # по обычному расписанию
            day_of_week = date.isoweekday()
            try:
                schedule = MasterSchedule.objects.get(master=master, day_of_week=day_of_week, is_active=True)
                work_start = schedule.start_time
                work_end = schedule.end_time
                use_regular_breaks = True
            except MasterSchedule.DoesNotExist:
                return []

        # Проверяем на рабочее время
        if not work_start or not work_end:
            return []

        # получаем перерывы
        time_offs = []

        if use_regular_breaks: # обычные перерывы
            day_of_week = date.isoweekday()
            time_offs = list(WeeklyTimeOff.objects.filter(
                master_id=master_id,
                day_of_week=day_of_week,
                is_active=True
            ))
        else:
            time_offs = special_breaks # спец перерывы

        bookings = Booking.objects.filter( # Получаем все существующие записи
            master=master,
            date=date,
            status__in=['pending', 'confirmed']
        ).order_by('time') # сортируем по времени

        slots = [] # делаем слоты
        current_time = datetime.combine(date, work_start)
        end_datetime = datetime.combine(date, work_end)
        service_duration = service.duration

        while current_time + timedelta(minutes=service_duration) <= end_datetime: # цикл пока насало рабочего дня и длительность услуги больше конца рабочего дня
            slot_start = current_time.time()
            slot_end = (current_time + timedelta(minutes=service_duration)).time()

            is_time_off = False # проверка пересечений с перерывами
            for time_off in time_offs:
                time_off_start = time_off.start_time
                time_off_end = time_off.end_time
                if (slot_start < time_off_end and slot_end > time_off_start): # если пересекаеться то недоступен
                    is_time_off = True
                    break

            is_booked = False # проверка на пересечение с дрегими записями
            for booking in bookings:
                booking_end = (datetime.combine(date, booking.time) +
                               timedelta(minutes=booking.service.duration)).time()
                if (slot_start < booking_end and slot_end > booking.time):
                    is_booked = True
                    break

            if not is_time_off and not is_booked: # если все не пересекаеься
                slots.append(current_time.time())

            current_time += timedelta(minutes=30) # следующтий слот

        return slots

    @staticmethod
    def is_slot_available(master_id, service_id, date, time): # проверяет доступно ли конкретное время
        available_slots = ScheduleService.get_available_slots(master_id, service_id, date)
        return time in available_slots
