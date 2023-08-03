from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response


from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    SubscribesSerializer,
    TagSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Subscribes, User


class SelfSubscribeError(APIException):
    """Ошибка подписки на самого себя."""

    status_code = 400
    default_detail = "Нельзя подписаться на самого себя."
    default_code = "bad request"


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление рецепта"""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly | IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["Post", "Delete"], name="favorite")
    def favorite(self, request, *args, **kwargs):
        """Добавить/удалить рецепт в избранное"""
        recipe_id = self.kwargs.get("pk")
        recipe = Recipe.objects.get(pk=recipe_id)
        if request.method == "POST":
            if Favorite.objects.filter(
                user=request.user, recipe__id=recipe_id
            ).exists():
                return Response(
                    {"errors": "Рецепт уже добавлен!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favorite.objects.create(recipe=recipe, user=self.request.user)
            serializer = RecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            instance = get_object_or_404(
                Favorite, recipe=recipe, user=self.request.user
            )
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["Post", "Delete"], name="Shopping_cart")
    def shopping_cart(self, request, *args, **kwargs):
        """Добавить/убрать рецепт в корзину"""
        recipe_id = self.kwargs.get("pk")
        user = request.user
        if request.method == "POST":
            if ShoppingCart.objects.filter(
                user=user, recipe__id=recipe_id
            ).exists():
                return Response(
                    {"errors": "Рецепт уже добавлен!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            recipe = get_object_or_404(Recipe, id=recipe_id)
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            instance = get_object_or_404(
                ShoppingCart, user=user, recipe__id=recipe_id)
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["Get"], name="Download Shopping_cart")
    def download_shopping_cart(self, request, *args, **kwargs):
        """Скачать файл с ингредиентами рецептов из корзины"""
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user_name = f"{user.first_name.title()}_" f"{user.last_name.title()}"
        ingredients = (
            IngredientInRecipe.objects.filter(
                recipe__shopping_cart__user=user
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(amount=Sum("amount"))
        )
        shopping_list = f"Список покупок для: {user_name}\n\n"
        shopping_list += "\n".join(
            [
                f'- {ingredient["ingredient__name"]} '
                f'({ingredient["ingredient__measurement_unit"]})'
                f' - {ingredient["amount"]}'
                for ingredient in ingredients
            ]
        )
        filename = f"{user.username}_shopping_list.txt"
        response = HttpResponse(shopping_list, content_type="text/plain")
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response


class TagViewSet(viewsets.ModelViewSet):
    """Представление тэгов"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientViewSet(viewsets.ModelViewSet):
    """Представление ингредиентов"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class UsersViewSet(DjoserUserViewSet):
    """Представление пользователей и подписок"""

    queryset = User.objects.all()
    serializer_class = SubscribesSerializer
    permission_classes = (IsAuthenticated,)

    @action(
        detail=False,
        methods=["Get"],
        permission_classes=[AllowAny],
        name="Subscriptions",
    )
    def subscriptions(self, request):
        """Список пользователей, на которых подписан юзер"""
        queryset = User.objects.filter(subscribed__user=request.user)
        serializer = SubscribesSerializer(
            queryset, context={"request": request}, many=True
        )
        return Response(serializer.data)

    @action(detail=True, methods=["Post", "Delete"], name="Subscribe")
    def subscribe(self, request, *args, **kwargs):
        """Подписаться/отписаться от пользователя"""
        subscribed_id = self.kwargs.get("id")
        author = get_object_or_404(User, pk=subscribed_id)
        if request.method == "POST":
            if author == self.request.user:
                raise SelfSubscribeError
            elif Subscribes.objects.filter(
                author=author, user=request.user
            ).exists():
                return Response(
                    {"errors": "Вы уже подписаны!"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscribes.objects.create(author=author, user=self.request.user)
            queryset = User.objects.filter(username=author)
            serializer = SubscribesSerializer(
                queryset, context={"request": request}, many=True
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            instance = get_object_or_404(
                Subscribes, author=author, user=request.user)
            instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
