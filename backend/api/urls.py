from django.urls import include, path, re_path
from djoser import views as djoser_views
from rest_framework.routers import DefaultRouter

from . import views
from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

router_v1 = DefaultRouter()

router_v1.register('tags', TagViewSet, basename='TagViewSet')
router_v1.register('recipes', RecipeViewSet, basename='RecipeViewSet')
router_v1.register(
    'ingredients', IngredientViewSet, basename='IngredientViewSet'
)

router_v1.register('users', UserViewSet, basename='UserViewSet')

urlpatterns = [
    path(
        'users/set_password/',
        djoser_views.UserViewSet.as_view({'post': 'set_password'}),
        name='userSetPassword',
    ),
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    re_path(
        r'recipes/(?P<id>[0-9]+)/shopping_cart',
        views.shopping_cart,
        name='ShoppingView',
    ),
    re_path(
        r'recipes/(?P<id>[0-9]+)/favorite', views.favorite, name='FavoriteView'
    ),
    re_path(
        r'users/(?P<id>[0-9]+)/subscribe',
        views.subscribe,
        name='SubscribeView',
    ),
    #     re_path(
    #         r'users/subscriptions',
    #         views.subscriptions,
    #         name='SubscriptionsView',
    #     ),
]
