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
    ),
    path(
        'user-objects-history/',
        users.views.UserOwnedObjectsOperationsHistoryView.as_view(),
        name='user-objects-history',
    ),
    path(
        'allowed-handle-entries/',
        users.views.AllowedToHandleEntries.as_view(),
        name='allowed-handle-entries',
    )
]