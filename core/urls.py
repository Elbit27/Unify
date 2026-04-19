from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Создаем роутер и регистрируем в нем наш ViewSet
router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('', views.frontpage, name='frontpage'),
    path('profile/', views.profile_view, name='profile'),
    path('api/', include(router.urls)),
]