from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import routers

from src.apps.core.views import ImageViewSet
from src.apps.user.views import AuthViewSet, UserViewSet

router = routers.SimpleRouter()
router.register('core/image', ImageViewSet, basename='image')
router.register('users', UserViewSet, basename='user')
router.register('auth', AuthViewSet, basename='auth')

urlpatterns = [
    path("", RedirectView.as_view(url="docs/")),
    path('', include(router.urls)),
    path("docs/", SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
