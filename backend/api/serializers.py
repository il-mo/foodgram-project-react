from django.contrib.auth.models import User
from rest_framework.relations import SlugRelatedField

from recipe.models import Follow, Ingredient, Recipe, Tag, IngredientInRecipe
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'colour', 'slug')
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField

    class Meta:
        fields = ('id', 'amount',)
        model = IngredientInRecipe
        read_only_fields = ('id', 'name',)


class RecipeSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(slug_field='username', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True)

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        model = Recipe


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault(),
    )
    following = serializers.SlugRelatedField(
        slug_field='username',
        default=serializers.CurrentUserDefault(),
        queryset=User.objects.all(),
    )

    def validate(self, data):
        if self.context['request'].user == data.get('author'):
            raise serializers.ValidationError('Нельзя подписаться на себя!')
        return data

    class Meta:
        fields = '__all__'
        model = Follow

    validators = [
        UniqueTogetherValidator(
            queryset=Follow.objects.all(), fields=('author', 'user')
        )
    ]
