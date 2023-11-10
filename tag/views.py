"""Views for the recipe APIs."""

from recipe import serializers
from core.models import Tag
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets


class TagViewSet(viewsets.ModelViewSet):
    """
    View for manage Tag APIs.
    """
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve tags for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')

    def perform_create(self, serializer):
        """
        Create a new Tag on DB.
        """
        serializer.save(user=self.request.user)