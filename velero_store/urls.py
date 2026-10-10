from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

from django.contrib import admin
from django.urls import path, include
from django.db import connection
from django.http import HttpResponse

# Vista temporal para probar la conexión
def diagnostico_db(request):
    db_name = connection.settings_dict['NAME']
    db_host = connection.settings_dict['HOST']
    return HttpResponse(f"Conectado a la BD: {db_name} en el host: {db_host}")

urlpatterns = [
    path('diagnostico-db/', diagnostico_db),  # <-- AQUÍ
    path('admin/', admin.site.urls),
    path('', include('catalog.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)