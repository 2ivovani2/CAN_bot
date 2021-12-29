from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from bot.views import BotView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('webhooks', csrf_exempt(BotView.as_view())),
]
