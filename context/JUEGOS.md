## **1\. Nivel Principiante: Pixel Roulette (Rojo, Negro o Número)**

**Por qué es el más fácil:** Es una operación matemática de un solo paso. Generas un número, comparas y pagas.

* **Lógica:**  
  * Generar un `random.randint(0, 36)`.  
  * 0 es **Verde** (Paga x35 si le atinan).  
  * Pares/Impares para **Rojo/Negro** (Paga x2).  
  * Número exacto (Paga x35).  
* **Desafío técnico:** Crear un formulario de Django que acepte múltiples tipos de apuesta en una sola vista.

## **2\. Nivel Intermedio Bajo: Classic 3-Slot (Horizontal)**

**Por qué sigue:** Solo comparas tres variables en una línea.

* **Lógica:**  
  * Generar una lista de 3 números: `[pos1, pos2, pos3]`.  
  * Si `pos1 == pos2 == pos3`, el usuario gana según el valor del símbolo.  
* **Desafío técnico:** Implementar el "Carrito de Fichas" antes de jugar, para que el usuario pueda recargar si se queda en cero.

## **3\. Nivel Intermedio Alto: Ravyn Grid (3x3 Slots)**

**Por qué sube de nivel:** Aquí entra la lógica de matrices y los multiplicadores apilables (stacking).

* **Lógica:**  
  * Generar una matriz de 3x3.  
  * Recorrer las 8 líneas posibles (3 horiz, 3 vert, 2 diag).  
  * **Multiplicadores:** Como mencionaste, usar los 4 símbolos (x0.5, x1.5, x2, x3). Si hay 3 líneas ganadoras, sumas los multiplicadores antes de aplicarlos a la apuesta.  
* **Desafío técnico:** El algoritmo de validación de líneas que no sea redundante y el respaldo JSON que devuelva la matriz completa al frontend.

## **4\. Nivel Experto: Pixel Blackjack**

**Por qué es el más difícil:** Es un juego de "estado". El servidor debe recordar qué cartas tiene el jugador y cuáles el dealer entre cada petición (Hit/Stand).

* **Lógica:**  
  * Manejo de un "Deck" (baraja) de 52 cartas.  
  * Lógica del As (vale 1 u 11).  
  * IA del Dealer (debe pedir carta hasta llegar a 17).  
* **Desafío técnico:** Uso intensivo de `request.session` para guardar la mano actual del jugador sin que se pierda al recargar la página.

