import cv2
import mediapipe as mp
import math

# 1. Preparar la IA
mp_manos = mp.solutions.hands
manos = mp_manos.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_dibujo = mp.solutions.drawing_utils

camara = cv2.VideoCapture(0)

while True:
    exito, frame = camara.read()
    if not exito:
        break

    frame = cv2.flip(frame, 1)
    # Necesitamos las dimensiones de la pantalla para convertir los puntos de la IA a píxeles
    alto, ancho, _ = frame.shape 
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    resultado = manos.process(frame_rgb)

    if resultado.multi_hand_landmarks:
        for mano_puntos in resultado.multi_hand_landmarks:
            mp_dibujo.draw_landmarks(frame, mano_puntos, mp_manos.HAND_CONNECTIONS)

            # 2. Extraer coordenadas en píxeles (para dibujar el cursor y calcular la pinza)
            x_pulgar, y_pulgar = int(mano_puntos.landmark[4].x * ancho), int(mano_puntos.landmark[4].y * alto)
            x_indice, y_indice = int(mano_puntos.landmark[8].x * ancho), int(mano_puntos.landmark[8].y * alto)
            x_corazon, y_corazon = int(mano_puntos.landmark[12].x * ancho), int(mano_puntos.landmark[12].y * alto)

            # 3. Lógica de "Dedo Estirado" (Comparamos la punta en Y con su nudillo inferior en Y)
            # El índice (punta 8 vs nudillo 6)
            indice_estirado = mano_puntos.landmark[8].y < mano_puntos.landmark[6].y
            # El corazón (punta 12 vs nudillo 10)
            corazon_estirado = mano_puntos.landmark[12].y < mano_puntos.landmark[10].y
            # El anular (punta 16 vs nudillo 14) -> Queremos que esté BAJADO (Y mayor que su nudillo)
            anular_bajado = mano_puntos.landmark[16].y > mano_puntos.landmark[14].y

            # Calculamos la distancia de la pinza (OK) para rotar
            distancia_ok = math.hypot(x_indice - x_pulgar, y_indice - y_pulgar)

            # 4. Lógica de tus controles
            # Gesto OK para rotar (prioridad 1)
            if distancia_ok < 40:
                cv2.putText(frame, "ROTAR PIEZA (OK)", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                print("¡Rotando!")
            
            # Modo arrastrar: Índice y corazón levantados, anular bajado (y no estar haciendo el OK)
            elif indice_estirado and corazon_estirado and anular_bajado and distancia_ok > 40:
                cv2.putText(frame, "ARRASTRANDO PIEZA", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)
                
                # Tu cursor será el punto medio entre el índice y el corazón
                centro_x = (x_indice + x_corazon) // 2
                centro_y = (y_indice + y_corazon) // 2
                
                # Dibujamos un círculo azul grande para que veas dónde "agarras" la pieza
                cv2.circle(frame, (centro_x, centro_y), 15, (255, 0, 0), cv2.FILLED)
                # Opcional: imprimir la coordenada en terminal, lo comento para que no sature la pantalla
                # print(f"Moviendo pieza a la coordenada X: {centro_x}")

    cv2.imshow("Prueba de Controles Tetris", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camara.release()
cv2.destroyAllWindows()