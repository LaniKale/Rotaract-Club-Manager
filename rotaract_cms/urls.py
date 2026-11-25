from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.templatetags.static import static as static_url
from django.urls import include, path
from django.views.generic import RedirectView

from members import account_views, application_views
from members.forms import EmailLoginForm
from members import views as member_views

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url=static_url('brand/favicon.ico'), permanent=True)),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(authentication_form=EmailLoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('join/', application_views.join, name='join'),
    path('account/password/', account_views.set_password, name='set_password'),
    path('roles/', include('members.role_urls')),
    path('', member_views.dashboard, name='dashboard'),
    path('members/', include('members.urls')),
    path('events/', include('events.urls')),
    path('attendance/', include('attendance.urls')),
]

# Serve uploaded flyers while developing (DEBUG = True).
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
