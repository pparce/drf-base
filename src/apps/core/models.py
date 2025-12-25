from django.db import models
from src.shared.models.base_model import BaseModel
# import blurhash
# from django_resized import ResizedImageField


class Image(BaseModel):
    # image = ResizedImageField(
    #     max_length=500,
    #     force_format="WEBP",
    #     quality=50,
    #     upload_to="images/",
    #     null=True,
    #     blank=True,
    # )
    image = models.ImageField(
        upload_to="images/",
        null=True,
        blank=True,
    )
    height = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=0)
    image_hash = models.CharField(max_length=64, blank=True, editable=False)

    def __str__(self):
        return self.image.name

    # def save(self, *args, **kwargs):
    #     if not self.image_hash:
    #         with self.image.open() as image_file:
    #             self.image_hash = blurhash.encode(image_file, x_components=4, y_components=4)
    #             super().save(*args, **kwargs)
    #     else:
    #         super().save(*args, **kwargs)
