from django.urls import path

from . import role_views

app_name = 'roles'

urlpatterns = [
    path('', role_views.role_list, name='list'),
    path('new/', role_views.role_edit, name='add'),
    path('<int:pk>/', role_views.role_edit, name='edit'),
    path('<int:pk>/delete/', role_views.role_delete, name='delete'),
]
