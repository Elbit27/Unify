from django.contrib import admin
from .models import Faculty, Group, Department, Subject, User, SemesterSubject, SemesterPlan

admin.site.register(Faculty)
admin.site.register(Department)
admin.site.register(Group)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'credits')
    search_fields = ('name',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'group')
    search_fields = ('username', 'first_name', 'last_name')

class SemesterSubjectInline(admin.TabularInline):
    model = SemesterSubject
    extra = 10
    # Теперь это будет работать, так как мы определили search_fields выше
    autocomplete_fields = ['subject', 'teacher']

@admin.register(SemesterPlan)
class SemesterPlanAdmin(admin.ModelAdmin):
    list_display = ('group', 'course_number', 'semester')
    inlines = [SemesterSubjectInline]