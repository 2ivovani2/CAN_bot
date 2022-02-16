from django.contrib import admin
from django.urls import path

from bot.views import *
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index),
    path('parse_wb_product', parse_wb_data)
]
