"""Project root urlconf"""

from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings

from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi


#  Project level URLs
urlpatterns = [
    path('admin/', admin.site.urls),
    path('archives/', include('archives.urls')),
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
   re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

#  Debug toolbar URL's
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

