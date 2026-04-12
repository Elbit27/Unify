from django.contrib import admin
from .models import Lesson, Campus, Room, ScheduleSlot, Attendance

# Register your models here.
admin.site.register(Lesson)
admin.site.register(Campus)
admin.site.register(Room)
admin.site.register(ScheduleSlot)
admin.site.register(Attendance)