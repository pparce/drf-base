from django.db import connection
from django.db.utils import OperationalError
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health_check(request):
    try:
        connection.ensure_connection()
        db_status = "ok"
    except OperationalError:
        db_status = "unavailable"

    return Response({
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
    })
