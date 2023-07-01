from django.forms import EmailField
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.relations import SlugRelatedField
from rest_framework.validators import UniqueValidator

from users.models import User
from djoser.serializers import UserSerializer
from api.validators import validate_username

class UsersSerializers(UserSerializer):
    
    class Meta():
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'password']


class UsersCreateSerializers(UserSerializer):
    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all()),
                    validate_username]
    )

    email = serializers.EmailField(
        max_length=254,
        required=True,               
    )

    class Meta():
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
      