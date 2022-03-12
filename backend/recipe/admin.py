from django.contrib import admin

from users.models import Follow
from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'recipe', 'amount')
    search_fields = ('ingredient',)
    list_filter = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    fields = ['author', 'name', 'text', 'tags', 'image', 'cooking_time']
    list_display = (
        'pk',
        'name',
        'text',
        'image',
        'cooking_time',
        'author',
        'favorites',
    )

    @staticmethod
    def favorites(obj):
        return obj.favorite.filter(favorite=True).count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'colour')
    search_fields = ('name',)
    list_filter = ('slug',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'user')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe', 'shopping_cart', 'favorite')
