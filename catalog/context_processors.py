from .models import get_bcv_rate

def bcv_rate_context(request):
    """
    Hace que la variable 'bcv_rate' esté disponible automáticamente
    en todas las plantillas HTML del proyecto.
    """
    rate = get_bcv_rate()
    formatted_rate = f"{rate:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return {
        'bcv_rate': formatted_rate
    }