"""URL mapping for recipe api."""

from django.urls import (
    path,
    include
)

from rest_framework.routers import DefaultRouter

from recipe import views as recipe_views
from tag import views as tag_views
from ingredient import views as ingredient_views

router = DefaultRouter()

router.register('recipes', recipe_views.RecipeViewSet)
router.register('tags', tag_views.TagViewSet)
router.register('ingredients', ingredient_views.IngredientViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
]
