from django.urls import path

import users.views

urlpatterns = [
    path(
        'entries/',
        users.views.UserEntries.as_view(),
        name='user-entries',
    )
]