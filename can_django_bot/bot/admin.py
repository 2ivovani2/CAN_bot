from django.contrib import admin
from .models import *

@admin.register(TGUser)
class TGUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'name', 'balance')
