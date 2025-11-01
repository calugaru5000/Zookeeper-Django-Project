# proj/zookeeper/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.AnimalListView.as_view(), name='animals_list'),
    path('animals/create/', views.AnimalCreateView.as_view(), name='animal_create'),
    path('animals/<int:pk>/', views.AnimalDetailView.as_view(), name='animal_detail'),
    path('animals/<int:pk>/update/', views.AnimalUpdateView.as_view(), name='animal_update'),
    path('animals/<int:pk>/delete/', views.AnimalDeleteView.as_view(), name='animal_delete'),
    path('animals/<int:pk>/feed/', views.feed_view, name='animal_feed'),
    # Map page
    path('map/', views.map_view, name='zoo_map'),
    
    # Admin URLs
    path('admin-dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    
    # Species Management
    path('species/create/', views.SpeciesCreateView.as_view(), name='species_create'),
    path('species/<int:pk>/update/', views.SpeciesUpdateView.as_view(), name='species_update'),
    path('species/<int:pk>/delete/', views.SpeciesDeleteView.as_view(), name='species_delete'),
    
    # Enclosure Management
    path('enclosures/create/', views.EnclosureCreateView.as_view(), name='enclosure_create'),
    path('enclosures/<int:pk>/update/', views.EnclosureUpdateView.as_view(), name='enclosure_update'),
    path('enclosures/<int:pk>/delete/', views.EnclosureDeleteView.as_view(), name='enclosure_delete'),
    
    # User Management
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
]