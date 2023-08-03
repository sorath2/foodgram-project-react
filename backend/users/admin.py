from django.contrib import admin

from .models import Subscribes, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
    )
    list_filter = (
        "username",
        "email",
    )


@admin.register(Subscribes)
class SubscribesAdmin(admin.ModelAdmin):
    list_display = (
        "author",
        "user",
    )
    list_filter = ("author",)
