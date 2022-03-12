from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models

from foodgram import settings


class Tag(models.Model):
    name = models.CharField(
        max_length=200, unique=True, verbose_name='Название'
    )
    slug = models.SlugField(unique=True)
    colour = ColorField(
        format='hexa', unique=True, verbose_name='Цветовой код'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200, verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=200, verbose_name='Единицы измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(max_length=200, verbose_name='Название рецепта')
    text = models.TextField(
        verbose_name='Описание рецепта', blank=True, null=True
    )
    image = models.ImageField(
        verbose_name='Изображение', upload_to='recipes/images/'
    )
    tags = models.ManyToManyField(Tag, related_name='recipes')
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientInRecipe', related_name='recipes'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления, минуты",
        validators=(
            MinValueValidator(
                1, message="Минимальное время приготовления - одна минута"
            ),
        ),
    )

    pub_date = models.DateTimeField(
        'Дата создания', auto_now_add=True, db_index=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество ингредиентов",
        validators=(
            MinValueValidator(
                1, message="Минимальное количество ингредиентов - 1"
            ),
        ),
    )

    class Meta:
        verbose_name = 'Добавить ингредиент в рецепт'
        verbose_name_plural = 'Добавить ингредиент в рецепт'
        ordering = ('recipe', 'ingredient')

    def __str__(self):
        return f'{self.ingredient.name}, {self.recipe.name}'


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorite',
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorite',
    )
    favorite = models.BooleanField(verbose_name='Избранное', default=False)
    shopping_cart = models.BooleanField(
        verbose_name='Корзина покупок', default=False
    )

    class Meta:
        verbose_name = 'Добавить рецепт в избранное/список покупок'
        verbose_name_plural = 'Добавить рецепт в избранное/список покупок'
