# backend/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, TrackViewSet, LicenseViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'users', UserViewSet)  # Registers /api/users/ and /api/users/<id>/
router.register(r'tracks', TrackViewSet)  # Registers /api/tracks/ and /api/tracks/<id>/
router.register(r'licenses', LicenseViewSet) # Registers /api/licenses/ and /api/licenses/<id>/

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # For login
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # For refreshing tokens
]