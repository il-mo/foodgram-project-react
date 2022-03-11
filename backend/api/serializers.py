from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, ParseError

from recipe.models import (
    Favorite,
    Follow,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    Tag,
)
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password',
        )
        model = User
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(
            author_id=obj.id, user_id=user.id
        ).exists()


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'colour', 'slug')
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        model = Recipe

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('ingredient_in_recipe__amount'),
        )
        return ingredients

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        recipe = Favorite.objects.filter(
            recipe_id=obj.id, user_id=user.id
        ).first()
        if recipe:
            return recipe.favorite
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        recipe = Favorite.objects.filter(
            recipe_id=obj.id, user_id=user.id
        ).first()
        if recipe:
            return recipe.shopping_cart
        return False

    def create(self, validated_data):
        tag_ids = Tag.objects.all().values_list('id', flat=True)
        tag_id = self.context.get('request').data['tags']

        for id in tag_id:
            if id not in tag_ids:
                raise ValidationError(
                    detail={'tags': ['Такого тэга не существует :(']}
                )

        recipe = super(RecipeSerializer, self).create(validated_data)

        for ingredient in self.initial_data['ingredients']:
            try:
                get_ingredient = Ingredient.objects.get(id=ingredient['id'])
                IngredientInRecipe.objects.update_or_create(
                    recipe=recipe,
                    ingredient=get_ingredient,
                    amount=ingredient['amount'],
                )
            except Ingredient.DoesNotExist:
                raise ValidationError(
                    detail={
                        'ingredients': ['Такого ингредиента не существует :(']
                    }
                )

        return recipe
        # recipe, created = Recipe.objects.update_or_create(
        #     name=validated_data['name'],
        #     author=validated_data['author'],
        #     text=validated_data['text'],
        #     image=validated_data['image'],
        #     cooking_time=validated_data['cooking_time'],
        #
        # )
        # for tag_id in validated_data['tags']:
        #     try:
        #         tag = Tag.objects.get(id=tag_id)
        #     except Exception:
        #         raise ParseError(
        #             detail={'tags': ['Такого тэга не существует :(']}
        #         )
        # recipe.tags.add(tag)
        #
        # for ingredient in self.initial_data['ingredients']:
        #     try:
        #         get_ingredient = Ingredient.objects.get(id=ingredient['id'])
        #         IngredientInRecipe.objects.update_or_create(
        #             recipe=recipe,
        #             ingredient=get_ingredient,
        #             amount=ingredient['amount'],
        #         )
        #     except Exception:
        #         raise ParseError(
        #             detail={
        #                 'ingredients': ['Такого ингредиента не существует :(']
        #             }
        #         )
        #
        # return recipe

class FollowSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        model = User

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(
            author_id=obj.id, user_id=user.id
        ).exists()

    def get_recipes(self, obj):
        try:
            count = int(self.context.GET['recipes_limit'])
            recipes = (
                Recipe.objects.filter(author_id=obj.id)
                .all()
                .prefetch_related(count)
            )
        except AttributeError:
            recipes = Recipe.objects.filter(author_id=obj.id).all()
        return FavoriteSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author_id=obj.id).count()