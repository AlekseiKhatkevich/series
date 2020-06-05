from django.urls import path
import archives.views

urlpatterns = [
    path('tvseries/', archives.views.TvSeriesListCreateView.as_view(), name='tvseries'),

]