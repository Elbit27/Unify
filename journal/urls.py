from django.urls import path
from . import views

urlpatterns = [
    path('', views.subject_list_view, name='journal-subjects'),
    path('<int:subject_id>/groups/', views.group_list_view, name='journal-groups'),
    path('<int:subject_id>/<int:group_id>/', views.teacher_journal_view, name='journal-view'),
    path('attendance/update/', views.update_attendance_ajax, name='update-attendance'),
]