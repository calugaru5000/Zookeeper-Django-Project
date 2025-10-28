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
]