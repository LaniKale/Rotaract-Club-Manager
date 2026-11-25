from django.urls import path

from . import views

app_name = 'events'

urlpatterns = [
    path('', views.event_list, name='list'),
    path('add/', views.event_add, name='add'),
    path('delete/', views.event_delete, name='delete'),
    path('removed/', views.removed_list, name='removed'),
    path('feed/', views.event_feed, name='feed'),
    path('<int:pk>/calendar.ics', views.event_ics, name='ics'),
]
