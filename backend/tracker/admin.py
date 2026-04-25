from django.contrib import admin
from .models import User, Sheep, Event


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "role", "is_staff")
    list_filter = ("role",)


@admin.register(Sheep)
class SheepAdmin(admin.ModelAdmin):
    list_display = ("tag_id", "origin_country", "batch_number", "created_at")
    search_fields = ("tag_id", "batch_number")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("sheep", "status", "location", "timestamp", "on_chain_verified")
    list_filter = ("status",)
