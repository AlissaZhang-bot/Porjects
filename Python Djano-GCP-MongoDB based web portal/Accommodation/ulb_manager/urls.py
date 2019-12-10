from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url
from backend import views

urlpatterns = [
    path('admin/', admin.site.urls), 
    path('', include('backend.urls')),
]
