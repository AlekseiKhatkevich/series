"""Project root urlconf"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter

import users.views

#  Move routing from Djoser app here in order to plug our custom view in case they needed.
djoser_router = DefaultRouter()
djoser_router.register('users', users.views.CustomDjoserUserViewSet)

#  Project level URLs
urlpatterns = [
    path('admin/', admin.site.urls),
    path('archives/', include('archives.urls')),

    #  Url to custom JWT token refresh endpoint. Overrides one url in 'djoser.urls.jwt'.
    re_path(r"^auth/jwt/refresh/?", users.views.CustomJWTTokenRefreshView.as_view(), name="jwt-refresh"),
    re_path(r'^auth/', include('djoser.urls.jwt')),
    # Change 'djoser.urls' in order to be able to use custom Views
    re_path(r'^auth/', include(djoser_router.urls)),
    #  re_path(r'^auth/', include('djoser.urls')),

    path('api-auth/', include('rest_framework.urls')),  # for basic auth in browsable apis
]

#  drf_yasg related settings.
schema_view = get_schema_view(
    openapi.Info(
        title="Series API",
        default_version='only one version',
        description="Api for my series archive.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="hardcase@inbox.ru"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.IsAuthenticated,),
)

#  drf_yasg related URl's
urlpatterns += [
    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json'
    ),
    re_path(
        r'^swagger/$',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'
    ),
    re_path(
        r'^redoc/$',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc'
    ),
]

#  Debug toolbar URL's
if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
