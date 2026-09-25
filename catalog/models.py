import requests
from django.db import models
from django.utils.text import slugify
from django.core.cache import cache
from multiselectfield import MultiSelectField


def get_bcv_rate():
    """
    Obtiene la tasa oficial BCV desde APIs públicas con caché de 5 minutos (300 segundos).
    """
    cached_rate = cache.get('bcv_rate')
    if cached_rate:
        return cached_rate

    rate = None

    # Intento 1 (subimos el timeout a 4 segundos)
    try:
        response = requests.get(
            'https://ve.dolarapi.com/v1/dolares/oficial', timeout=4
        )
        if response.status_code == 200:
            rate = float(response.json().get('promedio', 0))
    except Exception:
        pass

    # Intento 2 (si falla el primero)
    if not rate:
        try:
            response = requests.get(
                'https://rates.dolarvzla.com/bcv/current.json', timeout=4
            )
            if response.status_code == 200:
                rate = float(response.json().get('usd', 0))
        except Exception:
            pass

    # Valor por defecto actualizado (Coloca aquí la tasa real actual si las APIs fallan)
    if not rate or rate <= 0:
        rate = 850.56  # <--- Cambia este número por el valor real que deba tener si la API no responde

    # Guardar en caché por solo 300 segundos (5 minutos) 
    cache.set('bcv_rate', rate, 60) 
    return rate


SIZE_CHOICES = (
    ('TU', 'Talla Única'),
    ('SM', 'SM'),
    ('S', 'S'),
    ('M', 'M'),
    ('L', 'L'),
    ('XL', 'XL'),
    ('2XL', '2XL'),
    ('3XL', '3XL'),
)


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
    )
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Actual (Oferta)")
    compare_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, 
        verbose_name="Precio Anterior (Tachado)"
    )
    stock = models.PositiveIntegerField(default=10, verbose_name="Stock Disponible")
    is_active = models.BooleanField(
        default=True, verbose_name='¿Producto Activo?'
    )
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    sizes = MultiSelectField(
        choices=SIZE_CHOICES, default=['S', 'M', 'L', 'XL']
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def is_sold_out(self):
        """Devuelve True si el stock es 0 (Agotado)."""
        return self.stock == 0

    @property
    def on_sale(self):
        """Verifica si el producto tiene un precio anterior mayor al actual (está en oferta)."""
        return self.compare_price and self.compare_price > self.price

    @property
    def discount_percentage(self):
        """Calcula el porcentaje de descuento entero para mostrarlo en la interfaz."""
        if self.on_sale:
            discount = ((self.compare_price - self.price) / self.compare_price) * 100
            return int(round(discount))
        return 0

    @property
    def price_bs(self):
        """Calcula el precio actual en Bolívares de forma instantánea usando el valor en caché."""
        rate = get_bcv_rate()
        amount_bs = float(self.price) * rate
        return (
            f'{amount_bs:,.2f}'
            .replace(',', 'X')
            .replace('.', ',')
            .replace('X', '.')
        )

    @property
    def compare_price_bs(self):
        """Calcula el precio anterior (tachado) en Bolívares si aplica."""
        if self.compare_price:
            rate = get_bcv_rate()
            amount_bs = float(self.compare_price) * rate
            return (
                f'{amount_bs:,.2f}'
                .replace(',', 'X')
                .replace('.', ',')
                .replace('X', '.')
            )
        return None


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Suscriptor'
        verbose_name_plural = 'Suscriptores'

    def __str__(self):
        return self.email