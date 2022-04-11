from django.contrib import admin

from users.models import Follow

from .models import Favorite, Ingredient, IngredientInRecipe, Recipe, Tag


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    autocomplete_fields = ('recipe', 'ingredient')
    list_display = ('amount',)
    list_filter = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    fields = ('author', 'name', 'text', 'tags', 'image', 'cooking_time')
    list_display = (
        'pk',
        'name',
        'text',
        'image',
        'cooking_time',
        'author',
        'favorites',
    )
    search_fields = ('name',)

    @staticmethod
    def favorites(obj):
        return obj.favorite.filter(favorite=True).count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug', 'color')
    search_fields = ('name',)
    list_filter = ('slug',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'user')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    autocomplete_fields = ('recipe',)
    list_display = ('pk', 'user', 'shopping_cart', 'favorite')
