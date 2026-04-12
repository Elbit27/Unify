from django.urls import path
from . import views

urlpatterns = [
    path('', views.schedule_view, name="schedule"),
    path('generate/', views.generate_schedule_view, name="generate_schedule"),
    path('generate_slots/<int:group_id>/', views.generate_slots_view, name="generate_slots"),

]