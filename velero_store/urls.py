from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('catalog.urls')),
]

# Ruta dedicada para el video del preloader (evita que WhiteNoise bloquee el streaming)
urlpatterns += [
    re_path(r'^video-intro/(?P<path>.*)$', serve, {
        'document_root': settings.BASE_DIR / 'static' / 'img' / 'collections',
    }),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)