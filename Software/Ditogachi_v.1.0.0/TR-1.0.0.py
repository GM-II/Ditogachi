##  TR-1.0.0.py
##  This code belong to the Ditogachi's project by the Grupo de Microscopia, Intrumentación e Innovación GM-II
##  For more info please visit the group GitHub: https://github.com/GM-II
##
##  It's the code who allow us to anlyse the image data matched with the force sensor data from hardware,
##  allowing use to made deep anlysis from the local and global elongation of the sample.
##
##  Note: Some debuggin was made to get the final v.1.0.0, the most important was the elimination
##  of the interval variable for match the data, now it's already matched for the RT code.
##  Copyright 2026 Grupo de Microscopía, Instrumentación e Innovación GM-II (S. Rosas, S. Triviño, C. Garzón)
##
##   Licensed under the Apache License, Version 2.0 (the "License");
##   you may not use this file except in compliance with the License.
##   You may obtain a copy of the License at
##
##       http://www.apache.org/licenses/LICENSE-2.0
##
##   Unless required by applicable law or agreed to in writing, software
##   distributed under the License is distributed on an "AS IS" BASIS,
##   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##   See the License for the specific language governing permissions and
##   limitations under the License.
import cv2
import numpy as np
import openpyxl
from openpyxl import Workbook
import time

# 1. Configuración inicial
video_path = 'video_sample.mp4'
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Error al abrir el video.")
    exit()

# Obtener dimensiones del video
ancho_original = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
alto_original = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Calcular factor de escala dinámico para videos HD/4K
def calcular_factor_escala(altura, ancho):
    # Para 1080p y resoluciones mayores
    if altura > 1080:
        return min(480 / altura, 960 / ancho)  # Limitar dimensiones máximas
    else:
        return 1  # Factor para resoluciones menores

factor_escala = calcular_factor_escala(alto_original, ancho_original)
print(f"Resolución original: {ancho_original}x{alto_original}")
print(f"Factor de escala aplicado: {factor_escala:.2f}")

fps = cap.get(cv2.CAP_PROP_FPS)
frames_por_intervalo = 1
# 2. Selección manual de puntos
def seleccionar_puntos(event, x, y, flags, param):
    global puntos_seleccionados, frame_mostrar
    if event == cv2.EVENT_LBUTTONDOWN:
        # Convertir coordenadas de la ventana redimensionada a coordenadas originales
        x_original = int(x / factor_escala)
        y_original = int(y / factor_escala)
        
        puntos_seleccionados.append([x_original, y_original])
        # Mostrar en la ventana redimensionada
        cv2.circle(frame_mostrar, (x, y), 2, (0, 255, 0), -1)
        cv2.imshow('Selecciona 2 puntos o presiona q para salir', frame_mostrar)

# 3. Leer primer frame y seleccionar puntos
ret, frame = cap.read()
if not ret:
    print("Error al leer el primer frame del video.")
    exit()

# Redimensionar para visualización manteniendo proporción
ancho_redim = int(ancho_original * factor_escala)
alto_redim = int(alto_original * factor_escala)
frame_mostrar = cv2.resize(frame.copy(), (ancho_redim, alto_redim))

puntos_seleccionados = []
cv2.namedWindow('Selecciona 2 puntos o presiona q para salir', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Selecciona 2 puntos o presiona q para salir', ancho_redim, alto_redim)
cv2.setMouseCallback('Selecciona 2 puntos o presiona q para salir', seleccionar_puntos)

while True:
    cv2.imshow('Selecciona 2 puntos o presiona q para salir', frame_mostrar)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or len(puntos_seleccionados) >= 2:
        break
cv2.destroyAllWindows()

if len(puntos_seleccionados) < 2:
    print("Se requieren exactamente 2 puntos.")
    exit()

# Los puntos ya están en coordenadas originales, no es necesario deshacer el redimensionamiento
pts = np.array(puntos_seleccionados, dtype=np.float32).reshape(-1, 1, 2)
old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
initial_distance = np.linalg.norm(pts[0] - pts[1])

# 5. Configurar Excel
wb = Workbook()
ws = wb.active
ws.title = "Desplazamiento"
ws.append(["Tiempo (s)", "Desplazamiento (px)", "Distancia (px)"])

# 6. Parámetros mejorados para Lucas-Kanade
lk_params = dict(
    winSize=(25, 25),
    maxLevel=3,
    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
)

# 7. Procesamiento del video
frame_count = 0
cv2.namedWindow('Tracking de Puntos', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Tracking de Puntos', ancho_redim, alto_redim)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 8. Calcular flujo óptico
    new_pts, status, _ = cv2.calcOpticalFlowPyrLK(
        old_gray, frame_gray, pts, None, **lk_params
    )

    # 9. Verificar y corregir seguimiento
    good_new = []
    for i, (pt, st) in enumerate(zip(new_pts, status)):
        if st == 1:  # Punto válido
            good_new.append(pt)
        else:  # Punto perdido: intentar recuperarlo
            # Buscar características cerca de la última posición conocida
            x, y = pts[i].ravel()
            patch = frame_gray[int(y)-10:int(y)+10, int(x)-10:int(x)+10]
            if patch.size > 0:
                corners = cv2.goodFeaturesToTrack(patch, 1, 0.01, 10)
                if corners is not None:
                    good_new.append(corners[0] + np.array([x-10, y-10]))
                else:
                    good_new.append(pts[i])  # Usar posición anterior como último recurso
            else:
                good_new.append(pts[i])
    
    pts = np.array(good_new, dtype=np.float32).reshape(-1, 1, 2)
    
    # 10. Actualizar referencia cada frame (mejor para seguimiento)
    old_gray = frame_gray.copy()
    
    # Refinar puntos cada 5 frames
    if frame_count % 5 == 0:
        pts = cv2.cornerSubPix(
            frame_gray, pts, (10, 10), (-1, -1),
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 20, 0.03)
        )

    # 11. Visualización y guardado de datos
    frame_visual = frame.copy()
    for i, pt in enumerate(pts):
        x, y = pt.ravel()
        cv2.circle(frame_visual, (int(x), int(y)), 8, (0, 255, 0), -1)
        cv2.putText(frame_visual, f'P{i+1}', (int(x)+10, int(y)+10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    cv2.line(frame_visual, tuple(pts[0].ravel().astype(int)), 
            tuple(pts[1].ravel().astype(int)), (0, 0, 255), 2)

    if frame_count % frames_por_intervalo == 0:
        current_distance = np.linalg.norm(pts[0] - pts[1])
        desplazamiento = current_distance - initial_distance
        tiempo_actual = frame_count / fps
        ws.append([tiempo_actual, desplazamiento, current_distance])
        
        cv2.putText(frame_visual, f'Despl: {desplazamiento:.2f}px', (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)

    # Redimensionar frame para visualización
    frame_mostrar = cv2.resize(frame_visual, (ancho_redim, alto_redim))
    cv2.imshow('Tracking de Puntos', frame_mostrar)
    frame_count += 1

    if cv2.waitKey(30) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
wb.save("resultas_elongation.xlsx")
print("Análisis completado. Datos guardados en 'results_elongation.xlsx'")
