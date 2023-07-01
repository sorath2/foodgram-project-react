from rest_framework import (
    filters,
    mixins,
    permissions,
    serializers,
    status,
    viewsets,
)
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import AccessToken

from api.serializers import (
    UsersSerializers,
)
from users.models import User
from djoser.views import UserViewSet

class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializers
    lookup_field = 'username'
    lookup_value_regex = '^[\w.@+-]+\Z'
    