"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from PasswordManager import views
from PasswordManager.views import CredentialListCreateView, CredentialDetailView, NotesListCreateView, NotesDetailView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    
    path('', views.home, name='home'),
    path('notes/', views.notes_page, name='notes_page'),
    path('admin/', admin.site.urls),
    path('statistics/', views.statistics_page, name='statistics_page'),
    
    path('api/credentials/', CredentialListCreateView.as_view(), name="credential-list"),
    path('api/credentials/<int:pk>/', CredentialDetailView.as_view(), name="credential-detail"),
    path('api/notes/', NotesListCreateView.as_view(), name="notes-list"),
    path('api/notes/<int:pk>/', NotesDetailView.as_view(), name="notes-detail"),
    
    path('api/statistics/', views.api_statistics, name='database-stats'),
    path('api/security-stats/', views.api_security_stats, name='api_security_stats'),

    path('login/', views.login_view, name='login_view'),
    path('chat/', views.chat_view, name='chat'),
]

