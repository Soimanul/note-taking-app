from django.urls import path
from . import views

# This file maps the views to specific URL endpoints.
urlpatterns = [
    path('register/', views.UserCreate.as_view(), name='user-register'),
    path('documents/', views.DocumentListCreate.as_view(), name='document-list-create'),
    path('documents/<uuid:pk>/', views.DocumentRetrieveUpdateDestroy.as_view(), name='document-detail'),
]