import re

from rest_framework import serializers

USERNAME_PATTERN_REGEX = r'^[\w.@+-]+\Z'


def validate_username(value: str) -> str:
    """Валидация поля username согласно шаблону."""

    match = re.fullmatch(USERNAME_PATTERN_REGEX, value)
    if not match:
        raise serializers.ValidationError(
            'Имя пользователя некорректно.',
        )
    return value
