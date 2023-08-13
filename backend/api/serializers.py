from django.db.models import F
from django.db import transaction
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from api.validators import validate_username
from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag
from users.models import Subscribes, User


class UsersSerializer(UserSerializer):
    """Сериализация пользователей"""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed"
        ]

    def get_is_subscribed(self, obj):
        """Проверка подписки"""
        user = self.context.get("request").user
        return not user.is_anonymous and Subscribes.objects.filter(
            user=user, author=obj).exists()


class UsersCreateSerializer(UserSerializer):
    """Сериализация создания пользователей"""

    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=[UniqueValidator(
            queryset=User.objects.all()), validate_username],
    )

    email = serializers.EmailField(
        max_length=254,
        required=True,
    )

    class Meta:
        model = User
        fields = ["email", "username", "first_name", "last_name", "password"]

    def create(self, validated_data):
        """Создание пользователя с хешированным паролем"""
        return User.objects.create_user(**validated_data)


class TagSerializer(serializers.ModelSerializer):
    """Сериализация тэгов"""

    class Meta:
        model = Tag
        fields = "__all__"


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализация ингредиентов"""

    class Meta:
        model = Ingredient
        fields = "__all__"


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализация ингредиентов в рецепте"""

    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ["id", "amount"]


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализация рецепта"""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]
        read_only_fields = ("__all__",)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализация имеющегося рецепта"""

    image = Base64ImageField()
    author = UsersSerializer()
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        ]

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.values(
            "id", "name", "measurement_unit",
            amount=F("ingredient_in_recipe__amount")
        )
        return ingredients

    def get_is_favorited(self, obj):
        user = self.context.get("request").user
        return not user.is_anonymous and user.favorite_user.filter(
            recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        return not user.is_anonymous and user.shopping_cart.filter(
            recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализация создания рецепта"""

    author = serializers.CharField(default=serializers.CurrentUserDefault())
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    ingredients = IngredientInRecipeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        ]

    @staticmethod
    def ingredient_create(recipe, ingredients):
        IngredientInRecipe.objects.bulk_create(
            [
                IngredientInRecipe(
                    ingredient=Ingredient.objects.get(id=ingredient["id"]),
                    recipe=recipe,
                    amount=ingredient["amount"],
                )
                for ingredient in ingredients
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.ingredient_create(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.ingredient_create(instance, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get("request")
        context = {"request": request}
        return RecipeReadSerializer(instance, context=context).data


class SubscribesSerializer(UsersSerializer):
    """Сериализация подписок"""

    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    email = serializers.EmailField(default=serializers.CurrentUserDefault())
    username = serializers.SlugField(default=serializers.CurrentUserDefault())
    first_name = serializers.SlugField(
        default=serializers.CurrentUserDefault())
    last_name = serializers.SlugField(
        default=serializers.CurrentUserDefault())

    class Meta:
        model = User
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        ]
        read_only_fields = ("__all__",)

    def validate_username(self, value):
        author = self.context.get("author")
        user = self.context.get("user")
        if self.context.get("request").method == "POST":
            if author == user:
                raise serializers.ValidationError(
                    f"Нельзя подписаться на самого себя!",
                )
            elif Subscribes.objects.filter(
                author=author, user=user
            ).exists():
                raise serializers.ValidationError(
                    f"Вы уже подписаны!",
                )
        return value

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        return not user.is_anonymous and Subscribes.objects.filter(
            user=user, author=obj).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit", "")
        recipes = obj.recipes.all()
        if limit:
            if not (limit.isdigit()):
                raise ValidationError(
                    {"recipes_limit": "Может быть только числом!"})
            recipes = recipes[: int(limit)]
        serializer = RecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data
