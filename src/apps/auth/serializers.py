from django.contrib.auth import authenticate
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["email"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been disabled.")
        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    password = serializers.CharField(min_length=8, write_only=True)
    receive_news = serializers.BooleanField(default=False)


class SendRestoreCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()


class RestorePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=8)
    new_password = serializers.CharField(min_length=8)


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField(
        help_text="Google ID token obtained from the Google Sign-In flow on the client side."
    )
