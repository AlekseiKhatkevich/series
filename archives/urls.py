from django.urls import path, register_converter
import archives.views
import archives.converters

register_converter(
    archives.converters.CommaSeparatedIntegersPathConverter,
    'int_list'
)

urlpatterns = [
    path(
        'tvseries/<int:series_pk>/upload-image/<str:filename>/',
        archives.views.FileUploadDeleteView.as_view(),
        name='upload'
    ),
    path(
        'tvseries/<int:series_pk>/delete-image/<int_list:image_pk>/',
        archives.views.FileUploadDeleteView.as_view(),
        name='delete-image'
    ),
    path(
        'tvseries/',
        archives.views.TvSeriesListCreateView.as_view(),
        name='tvseries'),
]