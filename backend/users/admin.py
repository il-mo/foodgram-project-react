from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    fields = [
        'email',
        'password',
        'role',
        'username',
        'first_name',
        'last_name',
    ]
    list_display = (
        'pk',
        'username',
        'email',
        'password',
        'last_login',
        'date_joined',
    )
    search_fields = ['username']
