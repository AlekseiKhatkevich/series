from django.urls import include, path, register_converter
from rest_framework import routers

import administration.converters
import administration.views

register_converter(
    administration.converters.ModelNameConverter,
    'model',
)

router = routers.SimpleRouter()
router.register(
    r'',
    administration.views.HistoryViewSet,
    basename='history',
)


urlpatterns = [
    path('logs/',
         administration.views.LogsListView.as_view(),
         name='logs',
         ),
    path(
        'history/<model:model_name>/<int:pk>/',
        include(router.urls)
    )
]
