
from django.contrib import admin
from django.urls import path, include
import doctor_app

urlpatterns = [
path('admin/', admin.site.urls),
path('', include('doctor_app.urls')),
]
