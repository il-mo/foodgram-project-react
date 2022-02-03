from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FollowViewSet, IngredientViewSet, RecipeViewSet, TagViewSet

router = DefaultRouter()

router.register('tags', TagViewSet, basename='TagViewSet')
router.register('recipes', RecipeViewSet, basename='RecipeViewSet')
router.register(
    r'recipes/(?P<recipes_id>\d+)', RecipeViewSet, basename='RecipeViewSet'
)
router.register('ingredients', IngredientViewSet, basename='IngredientViewSet')
router.register(
    r'ingredients/(?P<ingredient_id>\d+)',
    RecipeViewSet,
    basename='RecipeViewSet',
)
router.register(r'users/(?P<user_id>\d+)/subscribe', FollowViewSet, basename='FollowViewSet')


urlpatterns = [
    path('', include(router.urls)),
]
