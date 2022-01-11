from django.contrib import admin
from .models import *

@admin.register(TGUser)
class TGUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'name', 'balance')

@admin.register(Transaction)
class TransactionAdministration(admin.ModelAdmin):
    list_display = ('payment_id', 'amount', 'user')
