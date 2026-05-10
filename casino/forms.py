from django import forms
from .models import Perfil

class CompraFichasForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.perfil = kwargs.pop('perfil', None)
        self.total_a_pagar = kwargs.pop('total_a_pagar', 0)
        super().__init__(*args, **kwargs)

    def validar_compra(self):
        if not self.perfil:
            raise forms.ValidationError("Perfil de usuario no proporcionado.")
        
        if self.perfil.dinero_ficticio < self.total_a_pagar:
            raise forms.ValidationError("No tienes suficiente dinero ficticio para realizar esta compra.")
        
        return True

class ApuestaRuletaForm(forms.Form):
    TIPO_APUESTA_CHOICES = [
        ('numero', 'Número Exacto'),
        ('color', 'Color'),
    ]
    COLOR_CHOICES = [
        ('', '---'),
        ('rojo', 'Rojo'),
        ('negro', 'Negro'),
    ]
    
    tipo_apuesta = forms.ChoiceField(choices=TIPO_APUESTA_CHOICES, label="Tipo de Apuesta")
    numero = forms.IntegerField(min_value=0, max_value=36, required=False, label="Número (0-36)")
    color = forms.ChoiceField(choices=COLOR_CHOICES, required=False, label="Color")
    monto = forms.IntegerField(min_value=1, label="Fichas a apostar")

    def __init__(self, *args, **kwargs):
        self.perfil = kwargs.pop('perfil', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        tipo_apuesta = cleaned_data.get('tipo_apuesta')
        numero = cleaned_data.get('numero')
        color = cleaned_data.get('color')
        monto = cleaned_data.get('monto')

        if not self.perfil:
            raise forms.ValidationError("Perfil no proporcionado.")
            
        if monto and self.perfil.fichas < monto:
            raise forms.ValidationError("No tienes suficientes fichas para esta apuesta.")

        if tipo_apuesta == 'numero' and numero is None:
            self.add_error('numero', "Debes elegir un número entre 0 y 36.")
            
        if tipo_apuesta == 'color' and not color:
            self.add_error('color', "Debes elegir un color.")
            
        return cleaned_data
