from django.urls import path

from . import application_views, views

app_name = 'members'

urlpatterns = [
    path('', views.member_list, name='list'),
    path('add/', views.member_add, name='add'),
    path('removed/', views.removed_list, name='removed'),
    path('applications/', application_views.application_list, name='applications'),
    path('applications/<int:pk>/reject/', application_views.application_reject, name='application_reject'),
    path('<int:pk>/', views.member_detail, name='detail'),
    path('<int:pk>/edit/', views.member_edit, name='edit'),
    path('<int:pk>/remove/', views.member_remove, name='remove'),
    path('<int:pk>/restore/', views.member_restore, name='restore'),
    path('<int:pk>/reset-password/', views.member_reset_password, name='reset_password'),
]
