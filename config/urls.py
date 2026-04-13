from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from account.views import verify_code_view, complete_profile

account_patterns = [
    path('verify-code/', verify_code_view, name='account_verify_code'),
    path('complete-profile/', complete_profile, name='complete_profile'),

    path('', include('allauth.urls')),
]


urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include(account_patterns)),
    path('game/', include('game.urls')),
    path('schedule/', include('schedule.urls')),
    path('journal/', include('journal.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)