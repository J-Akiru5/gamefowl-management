"""
URL configuration for Gamefowl Management System.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.analytics.urls', namespace='analytics')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('fowl/', include('apps.fowl.urls', namespace='fowl')),
    path('fights/', include('apps.fights.urls', namespace='fights')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    except ImportError:
        pass
