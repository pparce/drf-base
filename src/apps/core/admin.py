from django.contrib import admin
from src.apps.core.models import Image


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ["id", "image", "width", "height", "image_hash"]
    search_fields = ["image"]
    readonly_fields = ["image_hash", "width", "height"]
