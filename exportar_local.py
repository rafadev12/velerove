import os
import django
from django.conf import settings

# Configuramos las variables antes de inicializar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'velero_store.settings')

# Forzamos los ajustes de base de datos directamente en la configuración de Django para evitar rastro de Postgres
settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(__file__), 'db.sqlite3'),
    }
}

django.setup()

from django.core.management import call_command

print("Generando backup completo desde SQLite local...")
with open('backup_data.json', 'w', encoding='utf-8') as f:
    call_command('dumpdata', 'catalog', natural_foreign=True, natural_primary=True, stdout=f)

print("¡Éxito! El archivo 'backup_data.json' se ha generado correctamente con categorías y productos.")