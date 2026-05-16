from django.contrib import admin

from mainapp.models import Service, Booking, PortfolioItem, Review
from .models import MasterSchedule, WeeklyTimeOff, MasterException


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin): # отображение модельки услуги
    list_display = ('title', 'price') # какие поля видны
    search_fields = ('title',) # поиск по
    filter_horizontal = ['masters']
    list_filter = ['masters']
    ordering = ('title',) # сортировка по


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin): # отображение модельки записи
    list_display = ('name', 'phone', 'service', 'date', 'time', 'created_at') # какие поля видны
    list_filter = ('date', 'service') # фильтр по
    search_fields = ('name', 'phone', 'service__title') # поиск по
    ordering = ('date', 'time') # сортировка по


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin): # отображение модельки портфолио
    list_display = ['title', 'is_featured', 'order', 'date_created'] # какие поля видны
    list_filter = ['is_featured'] # фильтр по
    list_editable = ['is_featured', 'order'] # какие поля можно редактировать в списке
    search_fields = ['title', 'description'] # поиск по
    fieldsets = ( # группировка полей в форме редактирования
        ('Основная информация', {
            'fields': ('title', 'image', 'description')
        }),
        ('Дополнительно', {
            'fields': ('client_name', 'is_featured', 'order')
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin): # отображение модельки оценок
    list_display = ['user', 'service', 'average_rating', 'created_at', 'is_public'] # какие поля видны
    list_filter = ['is_public', 'created_at', 'service'] # фильтр по
    search_fields = ['user__username', 'comment'] # поиск по
    list_editable = ['is_public'] # какие поля можно редактировать в списке


@admin.register(MasterSchedule)
class MasterScheduleAdmin(admin.ModelAdmin): # отображение модельки расписания мастера
    list_display = ['master', 'day_of_week', 'start_time', 'end_time', 'is_active'] # какие поля видны
    list_filter = ['master', 'day_of_week', 'is_active'] # фильтр по
    list_editable = ['is_active'] # какие поля можно редактировать в списке


@admin.register(WeeklyTimeOff)
class WeeklyTimeOffAdmin(admin.ModelAdmin): # отображение модельки перерывов
    list_display = ['master', 'get_day_display', 'start_time', 'end_time', 'reason', 'is_active'] # какие поля видны
    list_filter = ['master', 'day_of_week', 'is_active'] # фильтр по
    list_editable = ['is_active'] # какие поля можно редактировать в списке

    def get_day_display(self, obj): # чтоб вместо цифры выводил название дня
        return obj.get_day_of_week_display()

    get_day_display.short_description = 'День недели' # название колонки в списке


@admin.register(MasterException)
class MasterExceptionAdmin(admin.ModelAdmin): # отображение модельки исключений в расписании
    list_display = ['master', 'date', 'is_working', 'start_time', 'end_time',
                    'break_start', 'break_end', 'reason'] # какие поля видны
    list_filter = ['master', 'is_working', 'date'] # фильтр по
    search_fields = ['master__username', 'reason'] # поиск по
    date_hierarchy = 'date' # иерархия по датам
    list_editable = ['is_working'] # какие поля можно редактировать в списке

    fieldsets = ( # группировка полей в форме редактирования
        ('Основная информация', {
            'fields': ('master', 'date', 'is_working', 'reason')
        }),
        ('Рабочее время (если отличается)', {
            'fields': ('start_time', 'end_time'),
            'classes': ('collapse',),
        }),
        ('Специальные перерывы', {
            'fields': ('break_start', 'break_end', 'break_reason'),
            'classes': ('collapse',),
        }),
    )
