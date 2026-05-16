from django import forms
from django.contrib.auth import get_user_model
from django.db import models

class Service(models.Model): # услуги
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    masters = models.ManyToManyField(
        'authapp.User',
        limit_choices_to={'role': 'master'},
        related_name='services',
        verbose_name='Мастера',
        blank=True
    )
    duration = models.IntegerField(
        default=60,
        verbose_name='Длительность (минут)',
        help_text='Сколько минут занимает услуга'
    )

    class Meta:
        verbose_name = 'Услуги'
        verbose_name_plural = 'Услуги'

    def __str__(self):
        return self.title # в админке по названию

User = get_user_model()


class Booking(models.Model): # записи
    STATUS_CHOICES = [ # возможные статусы
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('completed', 'Выполнено'),
        ('cancelled', 'Отменено'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', verbose_name='Пользователь',
                             null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='Услуга')
    master = models.ForeignKey(
        'authapp.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings_as_master',
        verbose_name='Мастер',
        limit_choices_to={'role': 'master'}
    )
    name = models.CharField(max_length=100, verbose_name='Имя')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    date = models.DateField(verbose_name='Дата')
    time = models.TimeField(verbose_name='Время')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )

    class Meta:
        ordering = ['-date', '-time'] # сначала новые
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        unique_together = ['master', 'date', 'time'] # чтоб повторов небыло

    def __str__(self):
        master_name = self.master.get_full_name() if self.master else 'Не назначен' # либо фио мастера, либо неназначен выводит
        return f"{self.name} - {self.service.title} - {master_name} - {self.date}"



class PortfolioItem(models.Model): # портфолио
    title = models.CharField(max_length=200, verbose_name='Название работы')
    image = models.ImageField(upload_to='portfolio/', verbose_name='Фото работы')
    description = models.TextField(blank=True, verbose_name='Описание')
    client_name = models.CharField(max_length=100, blank=True, verbose_name='Имя клиента')
    date_created = models.DateField(auto_now_add=True, verbose_name='Дата добавления')
    is_featured = models.BooleanField(default=False, verbose_name='Показывать на главной')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Работа'
        verbose_name_plural = 'Портфолио'
        ordering = ['-is_featured', 'order', '-date_created'] # сортировка сначала новые

    def __str__(self):
        return self.title


class Review(models.Model): # отзывы
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review', verbose_name='Запись') # связь один к одному с записями
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name='Пользователь')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='reviews', verbose_name='Услуга')

    QUALITY_CHOICES = [(i, i) for i in range(1, 6)]

    # критерии оценки
    speed_rating = models.PositiveSmallIntegerField(choices=QUALITY_CHOICES, verbose_name='Скорость работы')
    quality_rating = models.PositiveSmallIntegerField(choices=QUALITY_CHOICES, verbose_name='Качество работы')
    design_rating = models.PositiveSmallIntegerField(choices=QUALITY_CHOICES, verbose_name='Дизайн')
    cleanliness_rating = models.PositiveSmallIntegerField(choices=QUALITY_CHOICES, verbose_name='Чистота/Стерильность')
    price_rating = models.PositiveSmallIntegerField(choices=QUALITY_CHOICES, verbose_name='Цена/Качество')

    comment = models.TextField(verbose_name='Комментарий', blank=True) # коментарий необязательный

    LIKES_CHOICES = [
        ('speed', 'Скорость'),
        ('quality', 'Качество'),
        ('design', 'Дизайн'),
        ('cleanliness', 'Чистота'),
        ('price', 'Цена'),
        ('master', 'Мастер'),
        ('atmosphere', 'Атмосфера'),
    ]
    likes = models.JSONField(default=list, verbose_name='Что понравилось')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата отзыва')
    is_public = models.BooleanField(default=True, verbose_name='Опубликован')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at'] # сначала новые

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.service.title}"

    def average_rating(self): # для средней оценки
        ratings = [
            self.speed_rating,
            self.quality_rating,
            self.design_rating,
            self.cleanliness_rating,
            self.price_rating
        ]
        return sum(ratings) / len(ratings)



class MasterSchedule(models.Model): # расписание мастеров
    master = models.ForeignKey(
        'authapp.User',
        on_delete=models.CASCADE,
        related_name='schedules',
        limit_choices_to={'role': 'master'},
        verbose_name='Мастер'
    )

    DAYS_OF_WEEK = [
        (1, 'Понедельник'),
        (2, 'Вторник'),
        (3, 'Среда'),
        (4, 'Четверг'),
        (5, 'Пятница'),
        (6, 'Суббота'),
        (7, 'Воскресенье'),
    ]

    day_of_week = models.IntegerField(
        choices=DAYS_OF_WEEK,
        verbose_name='День недели'
    )
    start_time = models.TimeField(verbose_name='Начало работы')
    end_time = models.TimeField(verbose_name='Конец работы')
    slot_duration = models.IntegerField(
        default=60,
        help_text='Длительность слота в минутах',
        verbose_name='Длительность слота'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активно')

    class Meta:
        verbose_name = 'Расписание мастера'
        verbose_name_plural = 'Расписания мастеров'
        unique_together = ['master', 'day_of_week'] # чтоб не было 2 записей к 1 мастеру на 1 день

    def __str__(self): # в словарь для скорости названия по числу
        days = dict(self.DAYS_OF_WEEK)
        return f"{self.master.get_full_name()} - {days[self.day_of_week]} {self.start_time}-{self.end_time}"


class WeeklyTimeOff(models.Model): # перерывы
    master = models.ForeignKey(
        'authapp.User',
        on_delete=models.CASCADE,
        related_name='weekly_time_offs',
        limit_choices_to={'role': 'master'},
        verbose_name='Мастер'
    )

    DAYS_OF_WEEK = [
        (1, 'Понедельник'),
        (2, 'Вторник'),
        (3, 'Среда'),
        (4, 'Четверг'),
        (5, 'Пятница'),
        (6, 'Суббота'),
        (7, 'Воскресенье'),
    ]

    day_of_week = models.IntegerField(
        choices=DAYS_OF_WEEK,
        verbose_name='День недели'
    )
    start_time = models.TimeField(verbose_name='Начало перерыва')
    end_time = models.TimeField(verbose_name='Конец перерыва')
    reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Причина',
        default='Обед'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активно')

    class Meta:
        verbose_name = 'Регулярный перерыв'
        verbose_name_plural = 'Регулярные перерывы'
        ordering = ['day_of_week', 'start_time']
        unique_together = ['master', 'day_of_week', 'start_time'] # чтоб небыло 2х перерывов в 1 время

    def __str__(self):
        days = dict(self.DAYS_OF_WEEK)
        return f"{self.master.get_full_name()} - {days[self.day_of_week]} {self.start_time}-{self.end_time} ({self.reason})"


class MasterException(models.Model): # исключения в расписании мастера
    master = models.ForeignKey(
        'authapp.User',
        on_delete=models.CASCADE,
        related_name='exceptions',
        limit_choices_to={'role': 'master'},
        verbose_name='Мастер'
    )

    date = models.DateField(verbose_name='Дата')
    is_working = models.BooleanField(default=False, verbose_name='Работает?')
    start_time = models.TimeField(null=True, blank=True, verbose_name='Начало работы')
    end_time = models.TimeField(null=True, blank=True, verbose_name='Конец работы')
    break_start = models.TimeField(null=True, blank=True, verbose_name='Начало перерыва')
    break_end = models.TimeField(null=True, blank=True, verbose_name='Конец перерыва')
    break_reason = models.CharField(max_length=200, blank=True, verbose_name='Причина перерыва')
    reason = models.CharField(max_length=200, blank=True, verbose_name='Причина исключения')

    class Meta:
        verbose_name = 'Исключение в расписании'
        verbose_name_plural = 'Исключения в расписании'
        unique_together = ['master', 'date'] # 1 исключение на 1 дату

    def __str__(self): # статус текстовый
        status = "не работает" if not self.is_working else "работает"
        if self.is_working and self.start_time and self.end_time:
            status = f"работает {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
            if self.break_start and self.break_end:
                status += f" (перерыв {self.break_start.strftime('%H:%M')}-{self.break_end.strftime('%H:%M')})"
        return f"{self.master.get_full_name()} - {self.date} ({status})"
