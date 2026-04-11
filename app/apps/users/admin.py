from django.contrib import admin
from .models import ClientProfile

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('client_code', 'first_name', 'last_name', 'phone_number', 'created_at')
    search_fields = ('client_code', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('client_code', 'created_at')
    list_filter = ('created_at',)
