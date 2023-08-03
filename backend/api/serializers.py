import base64

from django.core.files.base import ContentFile
from django.db.models import F
from djoser.serializers import UserSerializer
from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from users.models import Subscribes, User
from api.validators import validate_username


class Base64ImageField(serializers.ImageField):
    """Сериализация картинки"""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)
        return super().to_internal_value(data)


class UsersSerializer(UserSerializer):
    """Сериализация пользователей"""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["email", "id", "username", "first_name", "last_name", "is_subscribed"]

    def get_is_subscribed(self, obj):
        """Проверка подписки"""
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Subscribes.objects.filter(user=user, author=obj).exists()


class UsersCreateSerializer(UserSerializer):
    """Сериализация создания пользователей"""

    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all()), validate_username],
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
        user = User.objects.create_user(**validated_data)
        return user


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
        fields = ("id", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализация рецепта"""

    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]
        read_only_fields = ("__all__",)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализация имеющегося рецепта"""

    image = Base64ImageField(required=True)
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
            "id", "name", "measurement_unit", amount=F("ingredient_in_recipe__amount")
        )
        return ingredients

    def get_is_favorited(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return user.favorite_user.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализация создания рецепта"""

    author = serializers.CharField(default=serializers.CurrentUserDefault())
    image = Base64ImageField(required=True)
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
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

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
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
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        IngredientInRecipe.objects.bulk_create(
            [
                IngredientInRecipe(
                    ingredient=Ingredient.objects.get(id=ingredient["id"]),
                    recipe=instance,
                    amount=ingredient["amount"],
                )
                for ingredient in ingredients
            ]
        )
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get("request")
        context = {"request": request}
        return RecipeReadSerializer(instance, context=context).data


class SubscribesSerializer(UsersSerializer):
    """Сериализация подписок"""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    email = serializers.EmailField(default=serializers.CurrentUserDefault())
    username = serializers.SlugField(default=serializers.CurrentUserDefault())
    first_name = serializers.SlugField(default=serializers.CurrentUserDefault())
    last_name = serializers.SlugField(default=serializers.CurrentUserDefault())

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

    def get_is_subscribed(self, obj):
        return True

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit", "")
        recipes = obj.recipes.all()
        if limit:
            if not (limit.isdigit()):
                raise ValidationError({"recipes_limit": "Может быть только числом!"})
            recipes = recipes[: int(limit)]
        serializer = RecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data
