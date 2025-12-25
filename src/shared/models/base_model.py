from django.db import models
from src.shared.models.base_date import BaseDate


class BaseModel(BaseDate):
    class Meta:
        abstract = True