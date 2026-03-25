# 🕹️ Tetris IA Mano (AR) Tetris con realidad aumentada

Un clon del clásico Tetris reinventado con **Realidad Aumentada (AR)** y **Control por Gestos**. Juega usando tu cámara web y el movimiento de tus manos en el aire, sin necesidad de controlarlo con el teclado.

El proyecto está hecho en Python y junta tres herramientas clave: **OpenCV** (para capturar el vídeo), **MediaPipe** (para que la IA entienda qué hace tu mano) y **Pygame** (para mover los bloques y la lógica del juego).

<div align="center">
  <video src="https://raw.githubusercontent.com/dev-manuelp/Tetris_Show/main/Tetris_Show.mp4" controls autoplay loop muted></video>
</div>

## Lo más destacado del proyecto
* **Tú eres el fondo (AR):** El tablero tiene transparencia, así que las piezas caen directamente sobre la imagen en tiempo real de tu cuarto.
* **A prueba de temblores:** Le he metido un filtro matemático (un suavizado de frames) que estabiliza la pieza. Si te tiembla un poco el pulso en el aire, la pieza no se vuelve loca de un lado a otro.
* **Pieza fantasma:** Como juegas en el aire y es difícil calcular a ojo, hay una silueta abajo del todo que te chiva exactamente dónde va a aterrizar el bloque.
* **Juego completo:** Tiene sistema de puntuación, borrado de líneas, Game Over y un panel que te avisa de qué pieza viene después.

## Gestos para jugar

He diseñado los controles para que los gestos sean muy distintos entre sí y la cámara no se confunda:

* ✌️ **Mover a los lados:** Junta el índice y el corazón (Cual Jedi). Mueve la mano y la pieza te seguirá por la cuadrícula.
* 👌 **Rotar:** Haz el gesto de "OK" juntando las puntas del pulgar y el índice.
* ✊ **Caída rápida (Hard Drop):** Esconde los dedos como si cerraras un puño o hicieras el gesto de "comillas" . La pieza caerá de forma rápida.

*(Por cierto, si te cansas de mover los brazos, las flechas del teclado siguen funcionando como plan B).*

## Cómo probarlo en tu equipo

Solo necesitas tener Python 3 instalado. Abre tu terminal y sigue estos pasos:

```bash
# 1. Bájate el código y entra en la carpeta
git clone [https://github.com/dev-manuelp/Tetris_Show.git](https://github.com/dev-manuelp/Tetris_Show.git)
cd Tetris_Show

# 2. Instala las dependencias
pip install -r requirements.txt

# 3. Arranca el juego
python tetris.py