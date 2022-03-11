from django.http import HttpResponse
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.filters import RecipeFilter, IngredientFilter
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


class CustomUserViewSet(UserViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    pagination_class = PagePagination

    # @action(
    #     methods=['GET'],
    #     detail=False,
    #     permission_classes=[IsAuthenticated],
    #     url_path='me',
    # )
    # def show_profile(self, request):
    #     serializer = self.get_serializer(request.user)
    #     return Response(serializer.data)
    #
    # @action(
    #     methods=['GET'],
    #     detail=False,
    #     permission_classes=[IsAuthenticated],
    #     url_path='subscriptions',
    # )
    # def show_subscriptions(self, request):
    #     author_ids = Follow.objects.filter(
    #         user_id=self.request.user.id
    #     ).values_list('author', flat=True)
    #     data = self.filter_queryset(
    #         User.objects.filter(id__in=author_ids).all()
    #     )
    #     page = self.paginate_queryset(data)
    #     serializer = FollowSerializer(page, context=request, many=True)
    #     if page is not None:
    #         return self.get_paginated_response(serializer.data)
    #     return Response(serializer.data, {'filter': filter})
    #
    # @action(
    #     methods=['POST', 'DELETE'],
    #     detail=False,
    #     permission_classes=[IsAuthenticated],
    #     url_path='(?P<id>[0-9]+)/subscribe',
    # )
    # def subscribe(self, request, id):
    #     author = get_object_or_404(User, id=id)
    #
    #     if request.method == 'POST':
    #
    #         if Follow.objects.filter(
    #                 author_id=author.id, user_id=self.request.user.id
    #         ).exists():
    #             raise ValidationError(
    #                 detail={
    #                     'error': ['Вы уже подписаны на данного пользователя']
    #                 }
    #             )
    #         Follow.objects.create(
    #             author_id=author.id, user_id=self.request.user.id
    #         )
    #         serializer = FollowSerializer(author, context=request)
    #         return Response(serializer.data)
    #
    #     if request.method == 'DELETE':
    #         try:
    #             Follow.objects.get(
    #                 author_id=author.id, user_id=self.request.user.id
    #             ).delete()
    #             return Response(
    #                 {'status': 'Вы успешно отписались от пользователя'},
    #                 status=status.HTTP_200_OK,
    #             )
    #         except Exception:
    #             raise ValidationError(
    #                 detail={
    #                     'error': [
    #                         'Вы не были подписаны на данного пользователя'
    #                     ]
    #                 }
    #             )
    @action(detail=True, permission_classes=[IsAuthenticated], methods=['POST', 'DELETE'])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            if user == author:
                return Response({
                    'errors': 'Вы не можете подписываться на самого себя'
                }, status=status.HTTP_400_BAD_REQUEST)
            if Follow.objects.filter(user=user, author=author).exists():
                return Response({
                    'errors': 'Вы уже подписаны на данного пользователя'
                }, status=status.HTTP_400_BAD_REQUEST)

            follow = Follow.objects.create(user=user, author=author)
            serializer = FollowSerializer(
                follow, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if user == author:
                return Response({
                    'errors': 'Вы не можете отписываться от самого себя'
                }, status=status.HTTP_400_BAD_REQUEST)
            follow = Follow.objects.filter(user=user, author=author)
            if follow.exists():
                follow.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response({
                'errors': 'Вы уже отписались'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthor]
    pagination_class = PagePagination
    filterset_class = RecipeFilter

    # def get_queryset(self):
    #     is_favorite = Favorite.objects.filter(user=self.request.user, recipe_id=OuterRef('id'))
    #     return self.queryset.annotate(is_favorite=Exists(is_favorite))

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
        methods=['GET'],
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
        methods=['POST'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
    )
    def get_shopping_cart(self):
        data = dict()
        recipes = Recipe.objects.filter(
            favorite__user=self.request.user, favorite__shopping_cart=True
        ).all()
        if not recipes:
            raise ValidationError(
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
