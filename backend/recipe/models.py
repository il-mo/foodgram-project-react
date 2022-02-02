from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=200, unique=True, verbose_name='Название'
    )
    slug = models.SlugField(unique=True)
    colour_code = ColorField(
        format='hexa', unique=True, verbose_name='Цветовой код'
    )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200, verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=200, verbose_name='Единицы измерения'
    )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(max_length=200, verbose_name='Название рецепта')
    text = models.TextField(verbose_name='Описание рецепта')
    image = models.ImageField(
        verbose_name='Изображение', upload_to='media/recipes/images/'
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

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class IngredientInRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='ingredient_in_recipe'
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

class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe, related_name='shopping_cart', on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_list'
            )
        ]



