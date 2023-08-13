from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated, AllowAny
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
from api.utils import create_file_shopping_cart
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Subscribes, User


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

    @action(detail=True, methods=["POST", "DELETE"], name="favorite")
    def favorite(self, request, *args, **kwargs):
        """Добавить/удалить рецепт в избранное"""
        recipe_id = self.kwargs.get("pk")
        recipe = get_object_or_404(Recipe, pk=recipe_id)
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

    @action(detail=True, methods=["POST", "DELETE"], name="Shopping_cart")
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

    @action(detail=False, methods=["GET"], name="Download Shopping_cart")
    def download_shopping_cart(self, request, *args, **kwargs):
        """Скачать файл с ингредиентами рецептов из корзины"""
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ingredients = (
            IngredientInRecipe.objects.filter(
                recipe__shopping_cart__user=user
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(amount=Sum("amount"))
        )
        response = create_file_shopping_cart(user, ingredients)
        return response


class TagViewSet(viewsets.ModelViewSet):
    """Представление тэгов"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    """Представление ингредиентов"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class UsersViewSet(DjoserUserViewSet):
    """Представление пользователей и подписок"""

    queryset = User.objects.all()
    serializer_class = SubscribesSerializer
    permission_classes = (IsAuthenticated,)

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[AllowAny],
        name="Subscriptions",
    )
    def subscriptions(self, request):
        """Список пользователей, на которых подписан юзер"""
        pages = self.paginate_queryset(
            User.objects.filter(subscribed__user=request.user)
        )
        serializer = SubscribesSerializer(
            pages, context={"request": request}, many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=["POST", "DELETE"], name="Subscribe")
    def subscribe(self, request, *args, **kwargs):
        """Подписаться/отписаться от пользователя"""
        subscribed_id = self.kwargs.get("id")
        author = get_object_or_404(User, pk=subscribed_id)
        if request.method == "POST":
            queryset = User.objects.filter(username=author)
            serializer = SubscribesSerializer(
                queryset, context={"request": request,
                                   "author": author,
                                   "user": self.request.user
                                   }, data=request.data
            )
            serializer.is_valid(raise_exception=True)
            Subscribes.objects.create(author=author, user=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            instance = get_object_or_404(
                Subscribes, author=author, user=request.user
            )
            instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
