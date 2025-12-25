
from rest_framework import serializers
from src.apps.user.models import User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'


class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name']


class UserEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email',
                  'first_name', 'last_name', 'avatar']



