from django.urls import include, path, register_converter
from rest_framework import routers

import archives.converters
import archives.views

register_converter(
    archives.converters.CommaSeparatedIntegersPathConverter,
    'int_list',
)

router_1 = routers.SimpleRouter()
router_1.register(
    r'',
    archives.views.SeasonsViewSet,
    basename='seasonmodel',
)

router_2 = routers.SimpleRouter()
router_2.register(
    r'',
    archives.views.UserObjectPermissionView,
    basename='manage-permissions',
)

router_3 = routers.SimpleRouter()
router_3.register(
    r'tvseries/full-text-search',
    archives.views.FTSListViewSet,
    basename='full-text-search',
)


urlpatterns = [
    path(
        'tvseries/<int:series_pk>/', include([
                path(
                    'upload-image/<str:filename>/',
                    archives.views.FileUploadDeleteView.as_view(),
                    name='upload',
                ),
                path(
                    'delete-image/<int_list:image_pk>/',
                    archives.views.FileUploadDeleteView.as_view(),
                    name='delete-image',
                ),
                path(
                    '',
                    archives.views.TvSeriesDetailView.as_view(),
                    name='tvseries-detail',
                ),
                path('seasons/', include(router_1.urls))
        ])),
    path(
        'tvseries/',
        archives.views.TvSeriesListCreateView.as_view(),
        name='tvseries',
    ),
    path(
        'manage-permissions/',
        include(router_2.urls),
    )
]

urlpatterns += router_3.urls
