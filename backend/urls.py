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
from graphene_django.views import GraphQLView
from PasswordManager.schema import schema

urlpatterns = [
    
    path('', views.home, name='home'),
    path('notes/', views.notes_page, name='notes_page'),
    path('admin/', admin.site.urls),
    
    path('api/credentials/', CredentialListCreateView.as_view(), name="credential-list"),
    path('api/credentials/<int:pk>/', CredentialDetailView.as_view(), name="credential-detail"),
    path('api/notes/', NotesListCreateView.as_view(), name="notes-list"),
    path('api/notes/<int:pk>/', NotesDetailView.as_view(), name="notes-detail"),
    path('api/credentials/add/', views.add_credential_view, name='add_credential'),
    path('api/credentials/update/<int:cred_id>/', views.update_credential_view, name='update_credential'),
    path('api/credentials/delete/<int:cred_id>/', views.delete_credential_view, name='delete_credential'),
    path('api/notes/add/', views.add_note_view, name='add_note'),
    path('api/notes/update/<int:cred_id>/', views.update_note_view, name='update_note'),  # maybe shoule be note_id
    path('api/notes/delete/<int:note_id>/', views.delete_note_view, name='delete_note'),
    path('api/start-loop/', views.start_loop, name='start_loop'),
    path('api/stop-loop/', views.stop_loop, name='stop_loop'),

    path("graphql/", csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
]

