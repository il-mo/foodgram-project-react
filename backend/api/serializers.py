from django.contrib.auth import get_user_model
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ParseError, ValidationError

from recipe.models import (Favorite, Ingredient, IngredientInRecipe,
                           Recipe, Tag)
from users.models import User, Follow
from users.serializers import CustomUserSerializer


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
    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
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

    def validate(self, data):
        ingredients = data['ingredients']
        tags = data['tags']
        data_list = []
        for ingredient in ingredients:
            if ingredient['amount'] <= 0:
                raise serializers.ValidationError('INGREDIENT_MORE_ZERO')
            if ingredient in data_list:
                raise serializers.ValidationError('INGREDIENT_ADDED')
            else:
                data_list.append(ingredient)
        for tag in tags:
            if tag in data_list:
                raise serializers.ValidationError('TAG_ADDED')
            else:
                data_list.append(tag)
        if data['cooking_time'] <= 0:
            raise serializers.ValidationError('COOKING_TIME_MORE_ZERO')
        del data_list
        data['ingredients'] = ingredients
        data['tags'] = tags
        return data

    def add_ingredients(self, instance, **validated_data):
        ingredients = validated_data['ingredients']
        for ingredient in ingredients:
            IngredientInRecipe.objects.create(
                recipe=instance,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount'],
            )
        return instance

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        return self.add_ingredients(
            recipe,
            ingredients=ingredients,
        )

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance = self.add_ingredients(
            instance,
            ingredients=ingredients,
        )
        return super().update(instance)

    # def create(self, validated_data):
    #     tag_ids = Tag.objects.all().values_list('id', flat=True)
    #     tag_id = self.context.get('request').data['tags']
    #
    #     for id in tag_id:
    #         if id not in tag_ids:
    #             raise ValidationError(
    #                 detail={'tags': ['Такого тэга не существует :(']}
    #             )
    #
    #     recipe = super(RecipeSerializer, self).create(validated_data)
    #
    #     for ingredient in self.initial_data['ingredients']:
    #         try:
    #             get_ingredient = Ingredient.objects.get(id=ingredient['id'])
    #             IngredientInRecipe.objects.update_or_create(
    #                 recipe=recipe,
    #                 ingredient=get_ingredient,
    #                 amount=ingredient['amount'],
    #             )
    #         except Ingredient.DoesNotExist:
    #             raise ValidationError(
    #                 detail={
    #                     'ingredients': ['Такого ингредиента не существует :(']
    #                 }
    #             )
    #
    #     return recipe
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
