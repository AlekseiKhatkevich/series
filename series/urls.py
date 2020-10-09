"""Project root urlconf"""
import debug_toolbar
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
#from drf_yasg import openapi, views
from rest_framework import permissions, routers

import users.views

#  Move routing from Djoser app here in order to plug our custom view in case they needed.
djoser_router = routers.DefaultRouter()
djoser_router.register('users', users.views.CustomDjoserUserViewSet)

#  Project level URLs
urlpatterns = [
    path('administration/', include('administration.urls')),
    path('admin/', admin.site.urls),
    path('archives/', include('archives.urls')),
    path('user-resources/', include('users.urls')),

    #  Url to custom JWT token refresh endpoint. Overrides one url in 'djoser.urls.jwt'.
    re_path(r'^auth/jwt/refresh/?', users.views.CustomJWTTokenRefreshView.as_view(), name='jwt-refresh'),
    #  Url to JWT obtain endpoint. Overrides one url in 'djoser.urls.jwt'.
    re_path(r"^auth/jwt/create/?", users.views.CustomTokenObtainPairView.as_view(), name='jwt-create'),
    re_path(r'^auth/', include('djoser.urls.jwt')),
    # Change 'djoser.urls' in order to be able to use custom Views
    re_path(r'^auth/', include(djoser_router.urls)),


    path('api-auth/', include('rest_framework.urls')),  # for basic auth in browsable apis
]

#  drf_yasg related settings.
# schema_view = views.get_schema_view(
#     openapi.Info(
#         title='Series API',
#         default_version='only one version',
#         description='Api for my series archive.',
#         terms_of_service='https://www.google.com/policies/terms/',
#         contact=openapi.Contact(email='hardcase@inbox.ru'),
#         license=openapi.License(name='BSD License'),
#         #generator_class = drf_yasg.generators.OpenAPISchemaGenerator
#     ),
#     public=True,
#     permission_classes=(permissions.IsAuthenticated,),
# )

#  drf_yasg related URl's
# urlpatterns += [
#     re_path(
#         r'^swagger(?P<format>\.json|\.yaml)$',
#         schema_view.without_ui(cache_timeout=0),
#         name='schema-json'
#     ),
#     re_path(
#         r'^swagger/$',
#         schema_view.with_ui('swagger', cache_timeout=0),
#         name='schema-swagger-ui'
#     ),
#     re_path(
#         r'^redoc/$',
#         schema_view.with_ui('redoc', cache_timeout=0),
#         name='schema-redoc'
#     ),
# ]

#  Debug toolbar URL's
if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

