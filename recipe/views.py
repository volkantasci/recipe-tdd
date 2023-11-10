"""Views for the recipe APIs."""

from recipe import serializers
from core.models import Recipe
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets


class RecipeViewSet(viewsets.ModelViewSet):
    """
    View for manage Recipe APIs.
    """
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve recipes for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action in ['list', 'create', 'update', 'partial_update']:
            return serializers.RecipeSerializer

        return self.serializer_class
