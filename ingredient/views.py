"""
Ingredients API ViewSets
"""

from rest_framework.viewsets import  ModelViewSet
from rest_framework.permissions import IsAuthenticated
from core.models import Ingredient

from recipe.serializers import IngredientSerializer


class IngredientViewSet(ModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticated]
    queryset = Ingredient.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-name')