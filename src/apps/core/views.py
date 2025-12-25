from rest_framework import viewsets
from src.apps.core.models import Image
from src.apps.core.serializers import ImageSerializer


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
