from django.urls import path

from . import views

app_name = 'attendance'

urlpatterns = [
    path('meetings/', views.meeting_list, name='meetings'),
    path('meetings/add/', views.meeting_add, name='meeting_add'),
    path('meetings/<int:pk>/', views.meeting_detail, name='detail'),
    path('meetings/<int:pk>/start/', views.start_session, name='start'),
    path('meetings/<int:pk>/close/', views.close_session, name='close'),
    path('meetings/<int:pk>/qr.png', views.qr_image, name='qr_image'),
    path('meetings/<int:pk>/manual/', views.manual_checkin, name='manual'),
    path('records/<int:pk>/remove/', views.remove_record, name='remove_record'),
    path('checkin/<str:token>/', views.checkin, name='checkin'),
    path('mine/', views.my_attendance, name='mine'),
]
