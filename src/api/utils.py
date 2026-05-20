import secrets
from datetime import datetime
from rest_framework import serializers
from django.core.files.base import ContentFile
import base64


def convert_date_to_save(date):
    if date is not None:
        return datetime.strptime(date, "%d/%m/%Y, %H:%M:%S")
    return None


def generate_code():
    """Generate a cryptographically secure 6-digit reset code."""
    return str(secrets.randbelow(900000) + 100000)


def calculate_remaining_time_in_seconds(start_date, end_date):
    remaining_time = end_date - start_date
    return int(remaining_time.total_seconds())


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[-1].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def convert_from_base64_to_file(image, name):
    format, imgstr = image.split(";base64,")
    if format is not None:
        ext = format.split("/")[-1]
        data = ContentFile(base64.b64decode(imgstr), name=name + "." + ext)
        return data


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.context.get("request", None):
            fields = self.context["request"].query_params.get("fields", None)
            if fields:
                fields = fields.replace(" ", "").split(",")
                allowed = set(fields)
                existing = set(self.fields.keys())
                for field_name in existing - allowed:
                    self.fields.pop(field_name)
