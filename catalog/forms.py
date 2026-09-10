from django import forms
from .models import SIZE_CHOICES, Product


class ProductForm(forms.ModelForm):
    sizes = forms.MultipleChoiceField(
        choices=SIZE_CHOICES,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "hidden peer",
            }
        ),
        required=False,
        label="Tallas Disponibles",
    )

    class Meta:
        model = Product
        # Se elimina 'sizes' de esta lista para evitar el FieldError
        fields = [
            "name",
            "slug",
            "category",
            "description",
            "price",
            "stock",
            "image",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full bg-zinc-950 border border-zinc-800 text-white p-3 font-mono text-xs focus:border-white focus:outline-none transition-colors"
                }
            ),
            "slug": forms.TextInput(
                attrs={
                    "class": "w-full bg-zinc-950 border border-zinc-800 text-white p-3 font-mono text-xs focus:border-white focus:outline-none transition-colors"
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "w-full bg-zinc-950 border border-zinc-800 text-white p-3 font-mono text-xs focus:border-white focus:outline-none transition-colors"
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "w-full bg-zinc-950 border border-zinc-800 text-white p-3 font-mono text-xs focus:border-white focus:outline-none transition-colors",
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "w-full bg-zinc-950 border border-zinc-800 text-white p-3 font-mono text-xs focus:border-white focus:outline-none transition-colors"
                }
            ),
            "stock": forms.NumberInput(
                attrs={
                    "class": "w-full bg-zinc-950 border border-zinc-800 text-white p-3 font-mono text-xs focus:border-white focus:outline-none transition-colors"
                }
            ),
            "image": forms.ClearableFileInput(
                attrs={
                    "class": "w-full bg-zinc-950 border border-zinc-800 text-zinc-400 p-3 font-mono text-xs focus:border-white focus:outline-none transition-colors"
                }
            ),
        }