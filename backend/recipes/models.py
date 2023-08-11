from colorfield.fields import ColorField
from django.db import models

from users.models import User


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name="Название ингредиента",
        null=False,
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name="Единица измерения",
        null=False,
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("name", "measurement_unit"),
                name="name_measurement_unit",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name="Название тэга",
        null=False,
        unique=True,
    )
    color = ColorField(default='#FF0000')
    slug = models.CharField(
        max_length=200,
        verbose_name="Описание тэга",
        null=True,
        unique=True,
    )

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="recipes",
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Название рецепта",
        null=False,
    )
    image = models.ImageField(
        verbose_name="Изображение рецепта",
    )
    text = models.TextField(
        verbose_name="Описание рецепта",
        null=False,
    )
    tags = models.ManyToManyField(
        Tag,
        through="TagInRecipe",
        verbose_name="Тэги",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="IngredientInRecipe",
        verbose_name="Ингредиенты",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления",
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, verbose_name="Рецепт",
        related_name="recipe",
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name="Ингредиент",
        related_name="ingredient_in_recipe",
        on_delete=models.CASCADE,
    )
    amount = models.IntegerField(
        verbose_name="Количество",
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецепте"
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "recipe",
                    "ingredient",
                ),
                name="unique_recipe_ingredient",
            ),
        ]
        ordering = ("ingredient",)

    def __str__(self) -> str:
        return f"{self.recipe} - {self.ingredient}"


class TagInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        related_name="recipes",
        on_delete=models.CASCADE
    )
    tag = models.ForeignKey(
        Tag,
        verbose_name="Тэг",
        related_name="tag_in_recipe",
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Тэг рецепта"
        verbose_name_plural = "Тэги рецепта"
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "recipe",
                    "tag",
                ),
                name="unique_recipe_tag",
            ),
        ]
        ordering = ("tag",)

    def __str__(self) -> str:
        return f"{self.recipe} - {self.tag}"


class Favorite(models.Model):
    recipe = models.ForeignKey(
        Recipe, related_name="favorite_recipe", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, related_name="favorite_user", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "recipe",
                    "user",
                ),
                name="unique_favorite_recipe",
            ),
        ]
        ordering = ("recipe",)

    def __str__(self) -> str:
        return f"{self.user} - {self.recipe}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Корзина покупок"
        verbose_name_plural = "Корзина покупок"
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "user",
                    "recipe",
                ),
                name="unique_shopping_cart",
            )
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Корзину покупок'
