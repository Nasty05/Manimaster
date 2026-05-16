from datetime import datetime
from django import forms
from authapp.models import User
from .models import Booking, Review


class BookingForm(forms.ModelForm): # форма записи
    class Meta:
        model = Booking # связь с моделькой
        fields = ['name', 'phone', 'service', 'date', 'time']
        widgets = { # внешний вид полей
            'name': forms.TextInput(attrs={'placeholder': 'Ваше имя'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Ваш телефон'}),
            'service': forms.Select(),
            'date': forms.DateInput(attrs={'type': 'date', 'min': datetime.today().strftime('%Y-%m-%d')}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }


class ReviewForm(forms.ModelForm): # форма для отзывов
    class Meta:
        model = Review # связь с моделькой
        fields = [
            'speed_rating', 'quality_rating', 'design_rating',
            'cleanliness_rating', 'price_rating', 'comment', 'likes'
        ]
        widgets = {
            'speed_rating': forms.RadioSelect(attrs={'class': 'star-rating'}),
            'quality_rating': forms.RadioSelect(attrs={'class': 'star-rating'}),
            'design_rating': forms.RadioSelect(attrs={'class': 'star-rating'}),
            'cleanliness_rating': forms.RadioSelect(attrs={'class': 'star-rating'}),
            'price_rating': forms.RadioSelect(attrs={'class': 'star-rating'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите подробнее о вашем опыте...'
            }),
            'likes': forms.CheckboxSelectMultiple(attrs={'class': 'likes-checkbox'}),
        }


class CustomUserChangeForm(forms.ModelForm): # форма редактирования профиля
    class Meta:
        model = User # связь с моделькой
        fields = ('username', 'name', 'surname', 'email', 'phone_number')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'surname': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AssignRoleForm(forms.ModelForm): # форма админки
    class Meta:
        model = User
        fields = ('role',)
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'})
        }
