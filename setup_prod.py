import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'velero_store.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
u, created = User.objects.get_or_create(username='velero')
u.set_password('velerove123')
u.is_staff = True
u.is_superuser = True
u.is_active = True
u.save()

if created:
    print('>>> SUPERUSUARIO CREADO EXITOSAMENTE DESDE SCRIPT <<<')
else:
    print('>>> CONTRASEÑA DE SUPERUSUARIO ACTUALIZADA EXITOSAMENTE <<<')