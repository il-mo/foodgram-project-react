from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
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

    # def get_queryset(self):
    #
    #     queryset = Follow.objects.filter(user=self.request.user, author=author)
    #
    #     queryset = Follow.objects.all()
    #     author = self.request.query_params.get('author')
    #     is_subscribed = queryset.filter(user=self.request.user, author=author)
    #     return User.objects.annotate(is_subscribed=Exists(is_subscribed))
    #
    #     author_ids = Follow.objects.filter(user=self.request.user).values_list(
    #         'id', flat=True
    #     )
    #
    #     for id in author_ids:
    #         query = Follow.objects.filter(
    #             user_id=self.request.user.id, author_id=id
    #         )
    #
    #         return User.objects.annotate(is_subscribed=Subquery(query))
    #
    #     query = Follow.objects.filter(user_id=self.request.user.id).values(
    #         'author'
    #     )
    #     return User.objects.annotate(is_subscribed=Subquery(query))

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
        author_ids = Follow.objects.filter(
            user_id=self.request.user.id
        ).values_list('author', flat=True)
        data = self.filter_queryset(
            User.objects.filter(id__in=author_ids).all()
        )
        serializer = FollowSerializer(data, context=request, many=True)
        return Response(serializer.data)

    @action(
        methods=['POST', 'DELETE'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='(?P<id>[0-9]+)/subscribe',
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':

            if Follow.objects.filter(
                author_id=author.id, user_id=self.request.user.id
            ).exists():
                raise ValidationError(
                    detail={
                        'error': ['Вы уже подписаны на данного пользователя']
                    }
                )
            Follow.objects.create(
                author_id=author.id, user_id=self.request.user.id
            )
            serializer = FollowSerializer(author, context=request)
            return Response(serializer.data)

        if request.method == 'DELETE':
            try:
                Follow.objects.get(
                    author_id=author.id, user_id=self.request.user.id
                ).delete()
                return Response(
                    {'status': 'Вы успешно отписались от пользователя'},
                    status=status.HTTP_200_OK,
                )
            except Exception:
                raise ValidationError(
                    detail={
                        'error': [
                            'Вы не были подписаны на данного пользователя'
                        ]
                    }
                )


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

    # def get_queryset(self):
    #     is_favorite = Favorite.objects.filter(user=self.request.user).values('recipes').first()
    #     return Recipe.objects.all().annotate(is_favorite=Exists(is_favorite))

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
        methods=['GET'],
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
