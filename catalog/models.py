import requests
from django.db import models
from django.utils.text import slugify
from multiselectfield import MultiSelectField


def get_bcv_rate():
    """Obtiene la tasa oficial BCV desde APIs públicas."""
    try:
        response = requests.get(
            'https://ve.dolarapi.com/v1/dolares/oficial', timeout=2
        )
        if response.status_code == 200:
            return float(response.json().get('promedio', 0))
    except Exception:
        pass

    try:
        response = requests.get(
            'https://rates.dolarvzla.com/bcv/current.json', timeout=2
        )
        if response.status_code == 200:
            return float(response.json().get('usd', 0))
    except Exception:
        pass

    return 36.50


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
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=10)
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
    def price_bs(self):
        """Calcula el precio en Bolívares usando la tasa BCV."""
        rate = get_bcv_rate()
        amount_bs = float(self.price) * rate
        return (
            f'{amount_bs:,.2f}'
            .replace(',', 'X')
            .replace('.', ',')
            .replace('X', '.')
        )


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Suscriptor'
        verbose_name_plural = 'Suscriptores'

    def __str__(self):
        return self.email