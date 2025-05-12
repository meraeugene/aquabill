from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    # Redirect the homepage to the login page
    path('', lambda request: redirect('/accounts/login/', permanent=False)),
    path('accounts/', include('allauth.urls')),
    path('core/', include('core.urls')),  # Ensure core urls are prefixed to avoid conflict
    path('pwa/', include('pwa.urls')),  # Same for pwa to avoid conflict
]

# Media file serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
