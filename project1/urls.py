from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from project1 import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mainapp.urls', namespace='mainapp')),
    path('auth/', include('authapp.urls', namespace='authapp')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
