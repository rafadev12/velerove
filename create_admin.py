import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'velero_store.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = "velero"
email = "contacto@velerove.com"
password = "velerove123"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superusuario '{username}' creado exitosamente.")
else:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    print(f"Contraseña actualizada para '{username}'.")