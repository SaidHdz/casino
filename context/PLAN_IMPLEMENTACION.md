## **Fase 1: Cimientos y Estructura (Día 1\)**

El objetivo es tener el entorno listo y la estructura de carpetas que solicitaste.

1. **Entorno Virtual:** Crea tu venv y activa: `python -m venv venv`.  
2. **Instalación:** `pip install django==6.0.3`.  
3. **Scaffolding:**  
   * `django-admin startproject config .` (Para que `manage.py` quede en la raíz).  
   * `python manage.py startapp casino`.  
4. **Directorios:** Crea manualmente la carpeta `templates/` en la raíz y `static/` dentro de `casino/`.  
5. **Settings:** Configura `'DIRS': [BASE_DIR / 'templates']` en `TEMPLATES` y añade `'casino'` a `INSTALLED_APPS`.

---

## **Fase 2: El Corazón de los Datos (Modelos)**

Aquí definimos cómo se guarda el dinero y las fichas.

1. **Definir Modelos:** Implementa el modelo `Perfil` (vinculado a `User`) y `PaqueteFichas`.  
2. **Signals:** Crea un archivo `signals.py` para que cada que se cree un `User`, se cree automáticamente su `Perfil`.  
3. **Migraciones:** `python manage.py makemigrations` y `migrate`.  
4. **Admin:** Registra los modelos en `admin.py` para que puedas crear "Paquetes de Fichas" desde el panel de control.

---

## **Fase 3: Lógica del "Carrito" y Vistas (CBVs)**

Implementaremos la compra de fichas usando la lógica de vistas flexibles y respaldo JSON.

1. **Lógica del Carrito (Sesiones):**  
   * Crear una vista para añadir un `PaqueteFichas` a la sesión (`request.session['carrito']`).  
2. **Vista de Tienda (ListView):** Implementar la clase con el `try-except` de `TemplateDoesNotExist` que devuelve un `JsonResponse`.  
3. **Procesamiento de Compra:**  
   * Validar en el servidor: `if perfil.dinero_ficticio >= total_carrito:`.  
   * Actualizar saldos: Restar dinero, sumar fichas.  
   * Limpiar carrito.

---

## **Fase 4: Sistema de Recompensa Diaria**

Como mencionaste que al entrar te dan dinero, necesitamos un "Middleware" o una lógica en la Portada.

1. **Lógica de Entrada:** En la `PortadaView`, verifica la fecha de la `ultima_recarga` del perfil.  
2. **Validación:** Si han pasado más de 24 horas (o es el primer login del día), suma la cantidad fija de "Dinero Diario" al saldo del usuario.

---

## **Fase 5: Maquetación Pixel Art (Frontend)**

Aquí es donde el proyecto cobra vida visualmente.

1. **Base Global:** Crear `templates/base.html` con los bloques `{% block content %}`.  
2. **Diseño CSS:**  
   * Usa `image-rendering: pixelated;` para todas las imágenes.  
   * Aplica fuentes de Google Fonts como **"Press Start 2P"**.  
   * Crea clases para bordes tipo "escalón" (2px o 4px solidos sin redondeo).  
3. **Plantillas Hijas:**  
   * `portada.html`: El lobby con botones grandes para ir a la "Tienda" o "Jugar".  
   * `tienda.html`: Grid de tarjetas con los paquetes de fichas.

---

## **Fase 6: Pulido y Pruebas**

1. **Validación de Formularios:** Asegurar que nadie pueda comprar fichas con saldo negativo mediante `forms.py`.  
2. **Pruebas de Respaldo:** Borra temporalmente (o cambia el nombre) de `tienda.html` para comprobar que la vista responde con el JSON de respaldo que pidió tu profesor.  
3. **Carga de Datos:** Crea un script `seed.py` o usa un archivo `.json` con `loaddata` para tener paquetes de fichas listos al presentar.

