from rest_framework import viewsets, status
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
    FollowSerializer,
    IngredientSerializer,
    RecipeSerializer,
    TagSerializer,
    UserSerializer,
    FavoriteSerializer,
)
from recipe.models import (
    Follow,
    Ingredient,
    Recipe,
    Tag,
    ShoppingCart,
    Favorite,
)
from users.models import User


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

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
        queryset = Follow.objects.filter(user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(page, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        pass

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
    recipe = get_object_or_404(Recipe, id=id)
    data = ShoppingCart.objects.create(user_id=request.user.id, recipe_id=id)
    serializer = FollowSerializer(recipe, many=True)
    serializer.is_valid(data)
    return Response(serializer.data)


# recipes/(?P<id>[0-9]+)/favorite
@api_view(['POST', 'DELETE'])
def favorite(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    if request.method == 'POST':
        add_recipe = Favorite.objects.get_or_create(
            recipe_id=id, user_id=request.user.id
        )[0]
        if add_recipe.favorite:
            raise ParseError(
                detail={
                    'error': ['Рецепт уже добавлен в ваш список избранного']
                }
            )
        else:
            add_recipe.favorite = True
            add_recipe.save()
        serializer = FavoriteSerializer(recipe)
        return Response(serializer.data)

    if request.method == 'DELETE':
        try:
            Favorite.objects.get(
                recipe_id=id, user_id=request.user.id
            ).delete()
            return Response(
                {'status': 'Рецепт удален из избранного'},
                status=status.HTTP_200_OK,
            )
        except Exception:
            raise ParseError(
                detail={'error': ['Рецепта нет в вашем списке избранного']}
            )


# TODO:check and write_only

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
