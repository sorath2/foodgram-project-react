from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        verbose_name="Логин",
        help_text="Укажите логин",
        unique=True,
    )

    email = models.EmailField(
        max_length=254,
        verbose_name="Email address",
        help_text="Укажите email",
        unique=True,
        null=False,
    )

    first_name = models.CharField(
        max_length=150,
        verbose_name="Имя",
        help_text="Укажите Имя",
        blank=False,
    )

    last_name = models.CharField(
        max_length=150,
        verbose_name="Фамилия",
        help_text="Укажите Фамилию",
        blank=False,
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self) -> str:
        return self.username


class Subscribes(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор рецепта",
        related_name="subscribed",
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Подписанный юзер",
        related_name="subscriber",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=("author", "user"),
                name="unique_subscribes",
            ),
        ]
        ordering = ("author",)
