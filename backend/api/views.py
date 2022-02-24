from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ParseError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.paginations import PagePagination
from api.permissions import IsAuthor
from api.serializers import (
    FavoriteSerializer,
    FollowSerializer,
    IngredientSerializer,
    RecipeSerializer,
    TagSerializer,
    UserSerializer,
)
from recipe.models import (
    Favorite,
    Follow,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    Tag,
)
from users.models import User


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    pagination_class = PagePagination

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me',
    )
    def show_profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',
    )
    def show_subscriptions(self, request):
        author_list = set()
        for _ in Follow.objects.filter(
                user_id=self.request.user.id
        ).select_related('author'):
            author_list.add(_.author)
        data = self.filter_queryset(
            User.objects.filter(id__in=[i.id for i in author_list]).all()
        )
        serializer = FollowSerializer(data, context=request, many=True)
        return Response(serializer.data)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = PagePagination


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = PagePagination


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthor]
    pagination_class = PagePagination

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
            raise ParseError(
                detail={'error': ['Ваш список покупок пустой :(']}
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

        filename = f'{self.request.user.username}_shopping_list.txt'
        response = HttpResponse(data, content_type='text.txt; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    def perform_create(self, serializer):
        if 'tags' not in self.request.data:
            raise ParseError(
                detail={'tags': ['Это поле обязательно к заполнению']}
            )
        tag_id = self.request.data['tags']
        author = self.request.user
        serializer.save(author=author, tags=tag_id)

    def perform_update(self, serializer):
        if 'tags' not in self.request.data:
            raise ParseError(
                detail={'tags': ['Это поле обязательно к заполнению']}
            )
        tag_id = self.request.data['tags']
        serializer.save(tags=tag_id)

    def perform_destroy(self, instance):
        instance.delete()


# recipes/(?P<id>[0-9]+)/shopping_cart'
@api_view(['POST', 'DELETE'])
def shopping_cart(request, id):
    _recipe = get_object_or_404(Recipe, id=id)
    if request.method == 'POST':
        recipe = Favorite.objects.get_or_create(
            recipe_id=id, user_id=request.user.id
        )[0]
        if recipe.shopping_cart is True:
            raise ParseError(
                detail={'error': ['Вы уже добавили рецепт в список покупок.']}
            )
        else:
            recipe.shopping_cart = True
            recipe.save()
        serializer = FavoriteSerializer(_recipe)
        return Response(serializer.data)

    if request.method == 'DELETE':
        recipe = Favorite.objects.get(recipe_id=id, user_id=request.user.id)
        if recipe.shopping_cart is False:
            raise ParseError(
                detail={'error': ['Рецепт не добавлен в список покупок']}
            )
        else:
            recipe.shopping_cart = False
            recipe.save()
            return Response(
                {'status': 'Рецепт удален из списка покупок'},
                status=status.HTTP_200_OK,
            )


# recipes/(?P<id>[0-9]+)/favorite
@api_view(['POST', 'DELETE'])
def favorite(request, id):
    _recipe = get_object_or_404(Recipe, id=id)
    if request.method == 'POST':
        recipe = Favorite.objects.get_or_create(
            recipe_id=id, user_id=request.user.id
        )[0]
        if recipe.favorite:
            raise ParseError(
                detail={
                    'error': ['Рецепт уже добавлен в ваш список избранного']
                }
            )
        else:
            recipe.favorite = True
            recipe.save()
        serializer = FavoriteSerializer(_recipe)
        return Response(serializer.data)

    if request.method == 'DELETE':
        recipe = Favorite.objects.get(recipe_id=id, user_id=request.user.id)
        if recipe.favorite is False:
            raise ParseError(
                detail={'error': ['Рецепта нет в вашем списке избранного']}
            )
        else:
            recipe.favorite = False
            recipe.save()
            return Response(
                {'status': 'Рецепт удален из избранного'},
                status=status.HTTP_200_OK,
            )


# users/(?P<id>[0-9]+)/subscribe
@api_view(['POST', 'DELETE'])
def subscribe(request, id):
    author = get_object_or_404(User, id=id)
    if request.method == 'POST':
        Follow.objects.create(author_id=author.id, user_id=request.user.id)
        serializer = FollowSerializer(author, context=request)
        return Response(serializer.data)

    if request.method == 'DELETE':
        try:
            Follow.objects.get(
                author_id=author.id, user_id=request.user.id
            ).delete()
            return Response(
                {'status': 'Вы успешно отписались от пользователя'},
                status=status.HTTP_200_OK,
            )
        except Exception:
            raise ParseError(
                detail={
                    'error': ['Вы не были подписаны на данного пользователя']
                }
            )
