from django.urls import path

import administration.views

urlpatterns = [
    path('logs/',
         administration.views.LogsListView.as_view(),
         name='logs',
         ),
]
