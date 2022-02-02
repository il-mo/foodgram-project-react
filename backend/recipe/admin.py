from django.contrib import admin

from .models import Ingredient, IngredientInRecipe, Recipe, ShoppingCart, Tag


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    fields = (
        'name',
        'measurement_unit',
    )


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    fields = (
        'ingredient',
        'recipe',
        'amount',
    )

    search_fields = ('ingredient',)
    list_filter = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    fields = (
        'name',
        'text',
        'image',
        'tags',
        'cooking_time',
        'author',
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    fields = (
        'user',
        'recipe',
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    fields = (
        'name',
        'slug',
        'colour_code',
    )
