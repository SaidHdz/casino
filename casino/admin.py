from django.contrib import admin
from .models import Perfil, PaqueteFichas

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'dinero_ficticio', 'fichas')
    search_fields = ('usuario__username',)

@admin.register(PaqueteFichas)
class PaqueteFichasAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cantidad_fichas', 'precio_dinero_ficticio')