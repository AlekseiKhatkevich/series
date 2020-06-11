from django.urls import path
import archives.views

urlpatterns = [
    path(
        'tvseries/upload/<int:series_pk>/<str:filename>/',
        archives.views.FileUploadView.as_view(),
        name='upload'
    ),
    path(
        'tvseries/',
        archives.views.TvSeriesListCreateView.as_view(),
        name='tvseries'),
]