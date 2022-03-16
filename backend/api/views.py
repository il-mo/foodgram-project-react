from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly, AllowAny,
)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.paginations import PagePagination
from api.permissions import IsAuthor
from api.serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeSerializer,
    TagSerializer,
)
from recipe.models import Favorite, Ingredient, IngredientInRecipe, Recipe, Tag
from utils.to_pdf import get_pdf

User = get_user_model()


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = AllowAny
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    # permission_classes = AllowAny


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthor]
    pagination_class = PagePagination
    filterset_class = RecipeFilter

    @action(
        methods=['POST', 'DELETE'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='(?P<id>[0-9]+)/favorite',
    )
    def favorite(self, request, id):
        _recipe = get_object_or_404(Recipe, id=id)

        if request.method == 'POST':
            recipe = Favorite.objects.get_or_create(
                recipe_id=id, user_id=self.request.user.id
            )[0]
            if recipe.favorite:
                raise ValidationError(
                    detail={
                        'error': [
                            'Рецепт уже добавлен в ваш список избранного'
                        ]
                    }
                )
            else:
                recipe.favorite = True
                recipe.save()
            serializer = FavoriteSerializer(_recipe)
            return Response(serializer.data)

        if request.method == 'DELETE':
            recipe = Favorite.objects.get(
                recipe_id=id, user_id=self.request.user.id
            )
            if recipe.favorite is False:
                raise ValidationError(
                    detail={'error': ['Рецепта нет в вашем списке избранного']}
                )
            else:
                recipe.favorite = False
                recipe.save()
                return Response(
                    {'status': 'Рецепт удален из избранного'},
                    status=status.HTTP_200_OK,
                )

    @action(
        methods=['POST', 'DELETE'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='(?P<id>[0-9]+)/shopping_cart',
    )
    def shopping_cart(self, request, id):
        _recipe = get_object_or_404(Recipe, id=id)

        if request.method == 'POST':
            recipe = Favorite.objects.get_or_create(
                recipe_id=id, user_id=self.request.user.id
            )[0]
            if recipe.shopping_cart is True:
                raise ValidationError(
                    detail={
                        'error': ['Вы уже добавили рецепт в список покупок.']
                    }
                )
            else:
                recipe.shopping_cart = True
                recipe.save()
            serializer = FavoriteSerializer(_recipe)
            return Response(serializer.data)

        if request.method == 'DELETE':
            recipe = Favorite.objects.get(
                recipe_id=id, user_id=self.request.user.id
            )
            if recipe.shopping_cart is False:
                raise ValidationError(
                    detail={'error': ['Рецепт не добавлен в список покупок']}
                )
            else:
                recipe.shopping_cart = False
                recipe.save()
                return Response(
                    {'status': 'Рецепт удален из списка покупок'},
                    status=status.HTTP_200_OK,
                )

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
    )
    def get_shopping_cart(self, request):
        data = dict()
        recipes = Recipe.objects.filter(
            favorite__user=self.request.user, favorite__shopping_cart=True
        ).all()
        if not recipes:
            raise ValidationError(
                detail={'error': ['Ваш список покупок пуст :(']}
            )
        for recipe in recipes:
            ingredients = IngredientInRecipe.objects.filter(
                recipe=recipe
            ).all()
            for ingredient in ingredients:
                if f'{ingredient.ingredient.id}' in data:
                    data[f'{ingredient.ingredient.id}'][
                        'amount'
                    ] += ingredient.amount
                else:
                    data.update(
                        {
                            f'{ingredient.ingredient.id}': {
                                'name': ingredient.ingredient.name,
                                'measurement_unit': ingredient.ingredient.measurement_unit,
                                'amount': ingredient.amount,
                            }
                        }
                    )

        data = dict(sorted(data.items(), key=lambda item: item[1]['name']))
        return get_pdf(data)

    def perform_create(self, serializer):
        if 'tags' not in self.request.data:
            raise ValidationError(
                detail={'tags': ['Это поле обязательно к заполнению']}
            )
        tag_id = self.request.data['tags']
        author = self.request.user
        serializer.save(author=author, tags=tag_id)

    def perform_update(self, serializer):
        if 'tags' not in self.request.data:
            raise ValidationError(
                detail={'tags': ['Это поле обязательно к заполнению']}
            )
        tag_id = self.request.data['tags']
        serializer.save(tags=tag_id)

    def perform_destroy(self, instance):
        instance.delete()
