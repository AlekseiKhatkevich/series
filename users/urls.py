from django.urls import path

import users.views

urlpatterns = [
    path(
        'entries/',
        users.views.UserEntries.as_view(),
        name='user-entries',
    ),
    path(
        'operations-history/',
        users.views.UserOperationsHistoryView.as_view(),
        name='user-operations-history',
    )
]