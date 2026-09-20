import os
import django
from django.core.management import call_command

# Ajusta 'velerove.settings' si tu archivo de configuración tiene otro nombre principal
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'velero_store.settings')
django.setup()

with open('catalog/fixtures/productos.json', 'w', encoding='utf-8') as f:
    call_command('dumpdata', 'catalog.Product', natural_foreign=True, natural_primary=True, indent=4, stdout=f)

print("¡Exportado con éxito en UTF-8!")