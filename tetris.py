import pygame
import sys
import random
import cv2
import mediapipe as mp
import math
import numpy as np

pygame.init()
pygame.key.set_repeat(200, 50)

# --- INICIAR LA IA Y LA CÁMARA ---
mp_manos = mp.solutions.hands
manos = mp_manos.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_dibujo = mp.solutions.drawing_utils
camara = cv2.VideoCapture(0)

# --- CONFIGURACIÓN DEL TABLERO ---
COLUMNAS = 10
FILAS = 20
TAMANO_BLOQUE = 40 

ANCHO_VENTANA = COLUMNAS * TAMANO_BLOQUE
ALTO_VENTANA = FILAS * TAMANO_BLOQUE

# Colores y Transparencias
NEGRO = (0, 0, 0)
GRIS_OSCURO_ALFA = (40, 40, 40, 100) 
BLANCO = (255, 255, 255)
ROJO = (255, 0, 0)
OPACIDAD_CAMARA = 150 

pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
pygame.display.set_caption("Tetris AR - Control por IA (Premium)")
reloj = pygame.time.Clock()

fuente_grande = pygame.font.SysFont("Arial", 50, bold=True)
fuente_pequena = pygame.font.SysFont("Arial", 30)
fuente_mini = pygame.font.SysFont("Arial", 20)

FORMAS = [
    [[1, 1, 1, 1]], [[1, 1], [1, 1]], [[0, 1, 0], [1, 1, 1]],
    [[0, 1, 1], [1, 1, 0]], [[1, 1, 0], [0, 1, 1]],
    [[1, 0, 0], [1, 1, 1]], [[0, 0, 1], [1, 1, 1]]
]

COLORES = [
    (0, 255, 255), (255, 255, 0), (128, 0, 128),
    (0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 165, 0)
]

tablero = [[0 for _ in range(COLUMNAS)] for _ in range(FILAS)]
juego_terminado = False
puntuacion = 0 

tiempo_ultima_rotacion = 0
cooldown_rotacion = 500 

# --- FILTRO ANTI-TEMBLORES ---
historial_posiciones_x = []
SUAVIZADO_FRAMES = 5 

# --- SISTEMA DE SIGUIENTE PIEZA ---
def generar_pieza_aleatoria():
    indice = random.randint(0, len(FORMAS) - 1)
    return FORMAS[indice], COLORES[indice]

siguiente_forma, siguiente_color = generar_pieza_aleatoria()

def sacar_nueva_pieza():
    global siguiente_forma, siguiente_color
    forma = siguiente_forma
    color = siguiente_color
    x = COLUMNAS // 2 - len(forma[0]) // 2
    y = 0
    siguiente_forma, siguiente_color = generar_pieza_aleatoria()
    return forma, color, x, y

def hay_colision(forma, offset_x, offset_y):
    for y, fila in enumerate(forma):
        for x, celda in enumerate(fila):
            if celda:
                tab_x = offset_x + x
                tab_y = offset_y + y
                if tab_x < 0 or tab_x >= COLUMNAS or tab_y >= FILAS or tablero[tab_y][tab_x] != 0:
                    return True
    return False

# --- CALCULAR LA PIEZA FANTASMA ---
def calcular_y_fantasma(forma, x, y):
    fantasma_y = y
    while not hay_colision(forma, x, fantasma_y + 1):
        fantasma_y += 1
    return fantasma_y

def fijar_pieza(forma, color, offset_x, offset_y):
    for y, fila in enumerate(forma):
        for x, celda in enumerate(fila):
            if celda:
                tablero[offset_y + y][offset_x + x] = color

def rotar_pieza(forma):
    return [list(fila) for fila in zip(*forma[::-1])]

def eliminar_lineas_completas():
    global tablero, puntuacion
    lineas_completas = []
    for y in range(FILAS):
        if 0 not in tablero[y]:
            lineas_completas.append(y)
            
    if len(lineas_completas) > 0:
        flash_surf = pygame.Surface((ANCHO_VENTANA, TAMANO_BLOQUE))
        flash_surf.fill(BLANCO)
        flash_surf.set_alpha(150)
        for y in lineas_completas:
            pantalla.blit(flash_surf, (0, y * TAMANO_BLOQUE))
        pygame.display.flip()
        pygame.time.delay(100) 
        
        for y in lineas_completas:
            del tablero[y] 
            tablero.insert(0, [0 for _ in range(COLUMNAS)]) 
            
        if len(lineas_completas) == 1: puntuacion += 100
        elif len(lineas_completas) == 2: puntuacion += 300
        elif len(lineas_completas) == 3: puntuacion += 500
        elif len(lineas_completas) >= 4: puntuacion += 800

def reiniciar_juego():
    global tablero, juego_terminado, puntuacion, forma_actual, color_actual, pieza_x, pieza_y
    global siguiente_forma, siguiente_color, historial_posiciones_x
    tablero = [[0 for _ in range(COLUMNAS)] for _ in range(FILAS)]
    juego_terminado = False
    puntuacion = 0 
    historial_posiciones_x = []
    siguiente_forma, siguiente_color = generar_pieza_aleatoria()
    forma_actual, color_actual, pieza_x, pieza_y = sacar_nueva_pieza()

# Arrancamos la primera pieza
forma_actual, color_actual, pieza_x, pieza_y = sacar_nueva_pieza()
tiempo_acumulado = 0
velocidad_caida = 500

superficie_rejilla = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA), pygame.SRCALPHA)

def dibujar_cuadricula_transparente():
    superficie_rejilla.fill((0,0,0,0)) 
    for x in range(0, ANCHO_VENTANA, TAMANO_BLOQUE):
        pygame.draw.line(superficie_rejilla, GRIS_OSCURO_ALFA, (x, 0), (x, ALTO_VENTANA))
    for y in range(0, ALTO_VENTANA, TAMANO_BLOQUE):
        pygame.draw.line(superficie_rejilla, GRIS_OSCURO_ALFA, (0, y), (ANCHO_VENTANA, y))
    pantalla.blit(superficie_rejilla, (0,0))

def dibujar_tablero():
    for y in range(FILAS):
        for x in range(COLUMNAS):
            if tablero[y][x] != 0:
                pygame.draw.rect(pantalla, tablero[y][x], 
                                 (x * TAMANO_BLOQUE, y * TAMANO_BLOQUE, TAMANO_BLOQUE, TAMANO_BLOQUE))
                pygame.draw.rect(pantalla, NEGRO, 
                                 (x * TAMANO_BLOQUE, y * TAMANO_BLOQUE, TAMANO_BLOQUE, TAMANO_BLOQUE), 1)

# --- BUCLE PRINCIPAL ---
while True:
    tiempo_pasado = reloj.tick(25) 
    tiempo_actual = pygame.time.get_ticks()
    
    if not juego_terminado:
        tiempo_acumulado += tiempo_pasado

    fondo_ar = None

    # --- 1. CAPTURA Y PROCESAMIENTO DE CÁMARA ---
    exito, frame = camara.read()
    if exito:
        frame = cv2.flip(frame, 1) 
        alto_cam, ancho_cam, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = manos.process(frame_rgb)

        if resultado.multi_hand_landmarks and not juego_terminado:
            for mano_puntos in resultado.multi_hand_landmarks:
                x_pulgar = int(mano_puntos.landmark[4].x * ancho_cam)
                x_indice = int(mano_puntos.landmark[8].x * ancho_cam)
                
                y_indice = mano_puntos.landmark[8].y
                y_nudillo_indice = mano_puntos.landmark[6].y
                
                y_corazon = mano_puntos.landmark[12].y
                y_nudillo_corazon = mano_puntos.landmark[10].y

                indice_estirado = y_indice < y_nudillo_indice
                corazon_estirado = y_corazon < y_nudillo_corazon

                distancia_ok = math.hypot(x_indice - x_pulgar, int(y_indice * alto_cam) - int(mano_puntos.landmark[4].y * alto_cam))

                # 1. ROTAR (OK)
                if distancia_ok < 40:
                    velocidad_caida = 500
                    if tiempo_actual - tiempo_ultima_rotacion > cooldown_rotacion:
                        forma_rotada = rotar_pieza(forma_actual)
                        if not hay_colision(forma_rotada, pieza_x, pieza_y):
                            forma_actual = forma_rotada
                            tiempo_ultima_rotacion = tiempo_actual

                # 2. CAÍDA RÁPIDA (Garra/Medio Puño)
                elif not indice_estirado and not corazon_estirado:
                    velocidad_caida = 50

                # 3. MOVER (V - Índice y Corazón) CON SUAVIZADO
                elif indice_estirado and corazon_estirado:
                    velocidad_caida = 500
                    
                    centro_x = (x_indice + int(mano_puntos.landmark[12].x * ancho_cam)) // 2
                    
                    historial_posiciones_x.append(centro_x)
                    if len(historial_posiciones_x) > SUAVIZADO_FRAMES:
                        historial_posiciones_x.pop(0) 
                        
                    x_suavizado = sum(historial_posiciones_x) / len(historial_posiciones_x)
                    
                    columna_destino = int((x_suavizado / ancho_cam) * COLUMNAS)
                    columna_destino = max(0, min(COLUMNAS - 1, columna_destino))

                    if pieza_x < columna_destino and not hay_colision(forma_actual, pieza_x + 1, pieza_y):
                        pieza_x += 1
                    elif pieza_x > columna_destino and not hay_colision(forma_actual, pieza_x - 1, pieza_y):
                        pieza_x -= 1
                else:
                    velocidad_caida = 500
                    historial_posiciones_x.clear() 

        # Transición a Pygame
        frame_mostrar = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_escalado = cv2.resize(frame_mostrar, (ANCHO_VENTANA, ALTO_VENTANA))
        fondo_ar = pygame.surfarray.make_surface(np.transpose(frame_escalado, (1, 0, 2)))
        fondo_ar.set_alpha(OPACIDAD_CAMARA)

    # --- 2. CONTROLES DE TECLADO ---
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            camara.release()
            cv2.destroyAllWindows()
            pygame.quit()
            sys.exit()
            
        if evento.type == pygame.KEYDOWN:
            if juego_terminado and evento.key == pygame.K_r: reiniciar_juego()
            elif not juego_terminado:
                if evento.key == pygame.K_LEFT and not hay_colision(forma_actual, pieza_x - 1, pieza_y): pieza_x -= 1
                if evento.key == pygame.K_RIGHT and not hay_colision(forma_actual, pieza_x + 1, pieza_y): pieza_x += 1
                if evento.key == pygame.K_DOWN: velocidad_caida = 50
                if evento.key == pygame.K_UP:
                    forma_rotada = rotar_pieza(forma_actual)
                    if not hay_colision(forma_rotada, pieza_x, pieza_y): forma_actual = forma_rotada
        if evento.type == pygame.KEYUP:
            if evento.key == pygame.K_DOWN: velocidad_caida = 500

    # --- 3. GRAVEDAD ---
    if not juego_terminado and tiempo_acumulado > velocidad_caida:
        if not hay_colision(forma_actual, pieza_x, pieza_y + 1):
            pieza_y += 1
        else:
            fijar_pieza(forma_actual, color_actual, pieza_x, pieza_y)
            eliminar_lineas_completas()
            forma_actual, color_actual, pieza_x, pieza_y = sacar_nueva_pieza()
            if hay_colision(forma_actual, pieza_x, pieza_y):
                juego_terminado = True
        tiempo_acumulado = 0

    # --- 4. DIBUJAR PANTALLA ---
    pantalla.fill(NEGRO)
    if fondo_ar is not None: pantalla.blit(fondo_ar, (0, 0))
    
    dibujar_tablero()
    dibujar_cuadricula_transparente()
    
    if not juego_terminado:
        # DIBUJAR LA PIEZA FANTASMA AL FONDO
        fantasma_y = calcular_y_fantasma(forma_actual, pieza_x, pieza_y)
        for y, fila in enumerate(forma_actual):
            for x, celda in enumerate(fila):
                if celda:
                    pygame.draw.rect(pantalla, color_actual, 
                                     ((pieza_x + x) * TAMANO_BLOQUE, (fantasma_y + y) * TAMANO_BLOQUE, TAMANO_BLOQUE, TAMANO_BLOQUE), 2)

        # DIBUJAR LA PIEZA REAL CAYENDO
        for y, fila in enumerate(forma_actual):
            for x, celda in enumerate(fila):
                if celda:
                    pygame.draw.rect(pantalla, color_actual, 
                                     ((pieza_x + x) * TAMANO_BLOQUE, (pieza_y + y) * TAMANO_BLOQUE, TAMANO_BLOQUE, TAMANO_BLOQUE))
                    pygame.draw.rect(pantalla, NEGRO, 
                                     ((pieza_x + x) * TAMANO_BLOQUE, (pieza_y + y) * TAMANO_BLOQUE, TAMANO_BLOQUE, TAMANO_BLOQUE), 1)

    # --- DIBUJAR UI (Marcador y Siguiente Pieza) ---
    texto_puntos = fuente_pequena.render(f"Puntos: {puntuacion}", True, BLANCO)
    pantalla.blit(texto_puntos, (10, 10))

    panel_x = ANCHO_VENTANA - 120
    panel_y = 10
    pygame.draw.rect(pantalla, (0, 0, 0, 150), (panel_x, panel_y, 110, 110)) 
    pygame.draw.rect(pantalla, BLANCO, (panel_x, panel_y, 110, 110), 2) 
    texto_sig = fuente_mini.render("Siguiente:", True, BLANCO)
    pantalla.blit(texto_sig, (panel_x + 10, panel_y + 5))

    for y, fila in enumerate(siguiente_forma):
        for x, celda in enumerate(fila):
            if celda:
                pygame.draw.rect(pantalla, siguiente_color, 
                                 (panel_x + 15 + x * 20, panel_y + 35 + y * 20, 20, 20))
                pygame.draw.rect(pantalla, NEGRO, 
                                 (panel_x + 15 + x * 20, panel_y + 35 + y * 20, 20, 20), 1)

    if juego_terminado:
        over_surf = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA))
        over_surf.fill(NEGRO)
        over_surf.set_alpha(180)
        pantalla.blit(over_surf, (0,0))
        
        texto_fin = fuente_grande.render("GAME OVER", True, ROJO)
        texto_reinicio = fuente_pequena.render("Pulsa 'R' para jugar", True, BLANCO)
        pantalla.blit(texto_fin, (ANCHO_VENTANA // 2 - texto_fin.get_width() // 2, ALTO_VENTANA // 2 - 50))
        pantalla.blit(texto_reinicio, (ANCHO_VENTANA // 2 - texto_reinicio.get_width() // 2, ALTO_VENTANA // 2 + 20))

    pygame.display.flip()