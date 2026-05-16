# mainapp/urls.py
from django.urls import path

from . import views

app_name = 'mainapp'

urlpatterns = [
    path('', views.index, name='index'),
    path('services/', views.services_view, name='services'),
    path('portfolio/', views.portfolio_view, name='portfolio'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    path('add-review/<int:booking_id>/', views.add_review_view, name='add_review'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking_view, name='cancel_booking'),
    path('master-panel/', views.master_panel_view, name='master_panel'),
    path('admin-panel/', views.admin_panel_view, name='admin_panel'),
    path('admin-panel/change-role/<int:user_id>/', views.change_user_role_view, name='change_user_role'),
    path('get-masters/<int:service_id>/', views.get_masters_for_service, name='get_masters'),
    path('get-available-slots/', views.get_available_slots, name='get_available_slots'),
    path('master/schedule/', views.master_schedule_view, name='master_schedule'),
    path('master/update-booking/<int:booking_id>/', views.update_booking_status, name='update_booking_status'),
]
