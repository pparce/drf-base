from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend

class BaseModelViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"