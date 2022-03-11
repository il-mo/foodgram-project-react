from django.urls import include, path
from djoser import views as djoser_views
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    CustomUserViewSet,
)

router_v1 = DefaultRouter()

router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')

router_v1.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path(
        'users/set_password/',
        djoser_views.UserViewSet.as_view({'post': 'set_password'}),
        name='userSetPassword',
    ),
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
