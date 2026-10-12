import cv2
import numpy as np
import time
from openpyxl import Workbook
from datetime import datetime
import serial
import os
# Configuración de visualización
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480
#resolución
RESOLUCION = (960, 540)
#CALIDAD = 80
# Configuración del motor
MOTOR_FREQUENCY = 200  # Frecuencia inicial del motor en Hz
MOTOR_STOP_FREQUENCY = 0  # Frecuencia para detener el motor

# Umbrales de desplazamiento
X_THRESHOLD = 800  # píxeles (respecto al ROI inicial)
Y_THRESHOLD = 400  # píxeles (respecto al ROI inicial)
FRAME_TO_FRAME_THRESHOLDx = 3  # píxeles (entre frames consecutivos)
FRAME_TO_FRAME_THRESHOLDy = 3
# Inicializar ORB
orb = cv2.ORB_create(nfeatures=500, scaleFactor=1.2, nlevels=8, edgeThreshold=31, firstLevel=0, WTA_K=2, scoreType=cv2.ORB_HARRIS_SCORE, patchSize=31, fastThreshold=20)

# Inicializar la cámara principal
cap = cv2.VideoCapture(0)  # Usar la cámara predeterminada (cámara web)

# Inicializar la segunda cámara
cap2 = cv2.VideoCapture(1)  # Usar la segunda cámara (ajusta el índice según tu configuración)

# Verificar si las cámaras se abrieron correctamente
if not cap.isOpened():
    print("Error: No se pudo abrir la cámara principal.")
    exit()

if not cap2.isOpened():
    print("Error: No se pudo abrir la segunda cámara.")
    exit()

# Configurador de resolución a 720p para ambas camaras
cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUCION[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUCION[1])

cap2.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUCION[0])
cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUCION[1])

# Crear directorios para frames
os.makedirs('frames_macro', exist_ok=True)
os.makedirs('frames_micro', exist_ok=True)

frame_count = 0
# Variables para almacenar los últimos desplazamientos válidos
last_valid_displacement = 0.0
last_valid_dx = 0.0
last_valid_dy = 0.0

valor_leido = 0.0
newtons = 0.0
# Variables para almacenar el frame de referencia
reference_frame = None
reference_keypoints = None
reference_descriptors = None
roi = None  # Variable para almacenar la ROI

# Variables para el filtrado entre frames
prev_keypoints = None  # Almacena los keypoints del frame anterior

# Variable para controlar el tiempo
last_time = time.time()
interval = 0.3  # Intervalo de 0.3 segundo

# Umbral para ignorar desplazamientos pequeños (en píxeles)
displacement_threshold = 0.5  # Ignorar desplazamientos menores a 1 píxel

# Crear un archivo Excel para guardar los datos
wb = Workbook()
ws = wb.active
ws.title = "Deformación"
# Encabezados actualizados con todos los valores
ws.append(["Timestamp", 
           "Desplazamiento (px)", 
           "Valor leído", "Newtons", 
           "Desplazamiento X (px)", "Desplazamiento Y (px)"])  

# Variable para controlar la pausa
paused = False

# Configura el puerto serial (ajusta el puerto y el baud rate según tu configuración)
try:
    puerto_serial2 = serial.Serial('COM3', 115200, timeout=1)# Cambia 'COMX' por el puerto correcto
    # Esperar a que se establezca la conexión
    #time.sleep(1)
except serial.SerialException as e:
    print(f"Error al abrir el puerto serial: {e}")
    exit()

# Función para controlar el motor
def control_motor(frequency=None):
    try:
        if frequency is not None:
            puerto_serial2.write(f"{frequency}\n".encode())
        else:
            puerto_serial2.write("STOP\n".encode())
    except serial.SerialException as e:
        print(f"Error al enviar comando al motor: {e}")

# Función para encontrar el keypoint más cercano en el frame anterior
def find_closest_keypoint(current_point, prev_keypoints):
    """Encuentra el keypoint más cercano al punto actual en el frame anterior."""
    min_dist = float('inf')
    closest_pt = None
    for kp in prev_keypoints:
        dist = np.sqrt((current_point[0] - kp.pt[0])**2 + (current_point[1] - kp.pt[1])**2)
        if dist < min_dist:
            min_dist = dist
            closest_pt = kp.pt
    return closest_pt

# Función para mostrar matches con tamaño correcto
def show_matches(ref_frame, curr_frame, ref_kps, curr_kps, matches, max_height=600):
    h, w = ref_frame.shape
    scale = max_height / h
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    ref_resized = cv2.resize(ref_frame, (new_w, new_h))
    curr_resized = cv2.resize(curr_frame, (new_w, new_h))
    
    ref_kps_scaled = [cv2.KeyPoint(kp.pt[0]*scale, kp.pt[1]*scale, kp.size) 
                     for kp in ref_kps]
    curr_kps_scaled = [cv2.KeyPoint(kp.pt[0]*scale, kp.pt[1]*scale, kp.size) 
                      for kp in curr_kps]
    
    match_img = cv2.drawMatches(ref_resized, ref_kps_scaled,
                               curr_resized, curr_kps_scaled,
                               matches[:50], None,
                               flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    
    cv2.namedWindow('Matches', cv2.WINDOW_NORMAL)
    cv2.imshow('Matches', match_img)
    cv2.resizeWindow('Matches', new_w * 2, new_h)

# Función para capturar el frame de referencia y seleccionar la ROI
def capture_reference_frame():
    global reference_frame, reference_keypoints, reference_descriptors, roi, prev_keypoints, puerto_serial
    ret, frame = cap.read()
    if not ret:
        print("Error: No se pudo capturar el frame de referencia.")
        return False

    roi = cv2.selectROI("Selecciona la ROI", frame, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow("Selecciona la ROI")

    reference_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    reference_frame = reference_frame[int(roi[1]):int(roi[1] + roi[3]), int(roi[0]):int(roi[0] + roi[2])]

    reference_keypoints, reference_descriptors = orb.detectAndCompute(reference_frame, None)
    if reference_descriptors is None:
        print("Error: No se pudieron calcular los descriptores de referencia.")
        return False
    
    
    print("Frame de referencia capturado y ROI seleccionada. Motor iniciado.")
    print("Secuencia inciada.")
    
    try:
        puerto_serial = serial.Serial('COM11', 115200, timeout=1)
    except serial.SerialException as e:
        print(f"Error al abrir el puerto serial COM11: {e}")
        return False
    if paused:
        puerto_serial.close()
        control_motor(MOTOR_FREQUENCY)
    prev_keypoints = None
    return True
start_time=time.time()
# Capturar el frame de referencia y seleccionar la ROI inicial
if not capture_reference_frame():
    cap.release()
    cap2.release()
    cv2.destroyAllWindows()
    exit()
last_time = time.time()
time_in = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: No se pudo capturar el frame de la cámara principal.")
        break
    frame_display = cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
    
    ret2, frame2 = cap2.read()
    if not ret2:
        print("Error: No se pudo capturar el frame de la segunda cámara.")
        break
    frame2_display = cv2.resize(frame2, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
    
    frame_with_roi = frame.copy()
    if roi is not None:
        cv2.rectangle(frame_with_roi, (int(roi[0]), int(roi[1])), 
                      (int(roi[0] + roi[2]), int(roi[1] + roi[3])), (0, 255, 0), 2)
        
    if not paused:
        # Guardar frames como imágenes PNG (en lugar de usar VideoWriter)
        cv2.imwrite(f"frames_macro/frame_{frame_count:06d}.png", frame)
        cv2.imwrite(f"frames_micro/frame_{frame_count:06d}.png", frame2)
        frame_count += 1
    if paused:
        cv2.putText(frame_with_roi, "PAUSADO", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0, 0, 255), 2, cv2.LINE_AA)

    cv2.imshow('Camara meso', frame_with_roi)

    if paused:
        frame2_paused = frame2.copy()
        cv2.putText(frame2_paused, "PAUSADO", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow('Camara micro', frame2_paused)
    else:
        cv2.imshow('Camara micro', frame2)

        
    current_time = time.time()
    
    if not paused and current_time - last_time >= interval:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_roi = gray[int(roi[1]):int(roi[1] + roi[3]), int(roi[0]):int(roi[0] + roi[2])]

        keypoints, descriptors = orb.detectAndCompute(gray_roi, None)

        if descriptors is not None and reference_descriptors is not None:
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(reference_descriptors, descriptors)

            average_displacement = 0.0
            average_dx = 0.0
            average_dy = 0.0
            
            if len(matches) > 0:
                matches = sorted(matches, key=lambda x: x.distance)

                displacements = []
                dx_values = []
                dy_values = []
                
                for match in matches:
                    pt_ref = reference_keypoints[match.queryIdx].pt
                    pt_curr = keypoints[match.trainIdx].pt
                    
                    # 1. Filtro absoluto (vs ROI de referencia)
                    dx_abs = pt_curr[0] - pt_ref[0]
                    dy_abs = pt_curr[1] - pt_ref[1]
                    if abs(dx_abs) > X_THRESHOLD or abs(dy_abs) > Y_THRESHOLD:
                        continue

                    # 2. Filtro entre frames consecutivos (si hay datos previos)
                    if prev_keypoints is not None:
                        prev_pt = find_closest_keypoint(pt_curr, prev_keypoints)
                        if prev_pt is not None:
                            dx_frame = pt_curr[0] - prev_pt[0]
                            dy_frame = pt_curr[1] - prev_pt[1]
                            if abs(dx_frame) > FRAME_TO_FRAME_THRESHOLDx or abs(dy_frame) > FRAME_TO_FRAME_THRESHOLDy:
                                continue

                    # Si pasa ambos filtros, usa el punto
                    displacement = np.sqrt(dx_abs**2 + dy_abs**2)
                    displacements.append(displacement)
                    dx_values.append(dx_abs)
                    dy_values.append(dy_abs)

                if len(displacements) > 0:
                    average_displacement = np.mean(displacements)
                    average_dx = np.mean(dx_values)
                    average_dy = np.mean(dy_values)
                    
                                        
                    if average_displacement > displacement_threshold:
                        print(f"Desplazamiento: {average_displacement:.2f} px")
                        print(f"X: {average_dx:.2f} px")
                        print(f"Y: {average_dy:.2f} px")
                        
                        last_valid_displacement = average_displacement
                        last_valid_dx = average_dx
                        last_valid_dy = average_dy
                        
                    else:
                        print("Desplazamiento despreciable (ruido)")
                        average_displacement = last_valid_displacement
                        average_dx = last_valid_dx
                        average_dy = last_valid_dy
                        
                else:
                    print("Todos los matches descartados por filtros. Usando últimos valores válidos.")
                    average_displacement = last_valid_displacement
                    average_dx = last_valid_dx
                    average_dy = last_valid_dy
                    
            else:
                print("No se encontraron matches. Usando últimos valores válidos.")
                average_displacement = last_valid_displacement
                average_dx = last_valid_dx
                average_dy = last_valid_dy
                
            # Actualizar keypoints del frame anterior
            prev_keypoints = keypoints
            
            if len(matches) > 0:
                show_matches(reference_frame, gray_roi, reference_keypoints, keypoints, matches)
        else:
            print("No se pudieron calcular los descriptores. Usando últimos valores válidos.")
            average_displacement = last_valid_displacement
            average_dx = last_valid_dx
            average_dy = last_valid_dy
        
        # Leer datos del Arduino       
        linea = puerto_serial.readline().decode('utf-8').strip()
        if linea:
            partes = linea.split()
            if len(partes) >= 4:
                valor_leido = float(partes[2])
                newtons = float(partes[4])
                print(f"Fuerza:{newtons:.2f}")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        # Guardar todos los valores en el Excel (originales y suavizados)
        ws.append([timestamp, 
                  average_displacement, 
                  valor_leido, newtons,
                  average_dx, average_dy])

        last_time = current_time

    key = cv2.waitKey(1)
    if key & 0xFF == ord('p'):
        paused = not paused
        if paused:
            control_motor(None)
            control_motor(MOTOR_STOP_FREQUENCY)
            try:
                puerto_serial.close()
            except serial.SerialException as e:
                print(f"Error al cerrar el puerto serial: {e}")
            print("Pausado - Motor detenido completamente - serial de lectura cerrado")
        else:
            if not capture_reference_frame():
                break
            print("Continuando con nueva referencia. Motor iniciado.")

    if key & 0xFF == ord('q'):
        control_motor(None)
        control_motor(MOTOR_STOP_FREQUENCY)
        print("Finalizado - Motor detenido completamente")
        break
        
# Guardar el archivo Excel
tictoc = time.time() - time_in
print(f"Duración real:{tictoc:.4f}")
output_file = "analisis_deformación_smo.xlsx"
wb.save(output_file)
print(f"Datos guardados en {output_file}")

# Liberar recursos
cap.release()
#video_output.release()
cap2.release()
#video_output2.release()
cv2.destroyAllWindows()

try:
    puerto_serial.close()
    puerto_serial2.close()
except serial.SerialException as e:
    print(f"Error al cerrar el puerto serial: {e}")

fpsout = frame_count / tictoc
print("Proceso completado. Para crear los videos ejecuta:")
print(f"ffmpeg -r {fpsout:.2f} -i frames_macro/frame_%06d.png -c:v libx264 -pix_fmt yuv420p -vf fps=30 video_macro.mp4, poner comillas en el fps=30")
print(f"ffmpeg -r {fpsout:.2f} -i frames_micro/frame_%06d.png -c:v libx264 -pix_fmt yuv420p -vf fps=30 video_micro.mp4")
