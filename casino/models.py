from django.db import models
from django.contrib.auth.models import User

class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    dinero_ficticio = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00)
    fichas = models.PositiveIntegerField(default=0)
    ultima_recarga = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

class PaqueteFichas(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    cantidad_fichas = models.PositiveIntegerField()
    precio_dinero_ficticio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nombre} ({self.cantidad_fichas} fichas)"

    class Meta:
        verbose_name = "Paquete de Fichas"
        verbose_name_plural = "Paquetes de Fichas"
