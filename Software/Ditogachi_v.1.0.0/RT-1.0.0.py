import cv2
import numpy as np
import time
from openpyxl import Workbook
from datetime import datetime
import serial
import os
# Configuración de visualización
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 360
#resolución
RESOLUCION = (1280, 720) #(640, 360)
# Configuración del motor
MOTOR_FREQUENCY = 200  # Frecuencia inicial del motor en Hz
MOTOR_STOP_FREQUENCY = 0  # Frecuencia para detener el motor

# Umbrales de desplazamiento
#X_THRESHOLD = 640  # píxeles (respecto al ROI inicial)
#Y_THRESHOLD = 360  # píxeles (respecto al ROI inicial)
FRAME_TO_FRAME_THRESHOLDx = 1.5  # píxeles (entre frames consecutivos)
FRAME_TO_FRAME_THRESHOLDy = 1.5
# Inicializar ORB
orb = cv2.ORB_create(nfeatures=500,
    scaleFactor=1.2,
    nlevels=8,
    edgeThreshold=31,
    firstLevel=0,
    WTA_K=2,
    scoreType=cv2.ORB_HARRIS_SCORE,
    patchSize=31,
    fastThreshold=20)

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

# Configurador de resolución para ambas camaras
cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUCION[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUCION[1])

cap2.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUCION[0])
cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUCION[1])

# VERIFICAR resolución (solo para debug)
actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Resolución cámara 1: {actual_width}x{actual_height}")

actual_width2 = int(cap2.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_height2 = int(cap2.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Resolución cámara 2: {actual_width2}x{actual_height2}")

# Crear directorios para frames
os.makedirs('frames_macro', exist_ok=True)
os.makedirs('frames_micro', exist_ok=True)


# Variables para almacenar los últimos desplazamientos válidos
last_valid_displacement = 0.0
last_valid_dx = 0.0
last_valid_dy = 0.0
frame_count = 0
valor_leido = 0.0
newtons = 0.0
# Variables para almacenar el frame de referencia
reference_frame = None
reference_keypoints = None
reference_descriptors = None
roi = None  # Variable para almacenar la ROI

# Variables para el filtrado entre frames
prev_keypoints = None  # Almacena los keypoints del frame anterior


# Umbral para ignorar desplazamientos pequeños (en píxeles)
displacement_threshold = 0.15  # Ignorar desplazamientos menores a 1 píxel

# Crear un archivo Excel para guardar los datos
wb = Workbook()
ws = wb.active
ws.title = "Deformación"
# Encabezados actualizados con todos los valores
ws.append(["Timestamp",  
           "Valor leído", "Newtons", 
           "Desplazamiento (px)",
           "Desplazamiento X (px)", "Desplazamiento Y (px)", "Frame"])  

# Variable para controlar la pausa
paused = False

# Configura el puerto serial (ajusta el puerto y el baud rate según tu configuración)
try:
    puerto_serial2 = serial.Serial('COM3', 115200, timeout=1)# Cambia 'COMX' por el puerto correcto
    # Esperar a que se establezca la conexión
    time.sleep(0.25)
except serial.SerialException as e:
    print(f"Error al abrir el puerto serial: {e}")
    exit()
############################
try:
    puerto_serial = serial.Serial('COM11', 115200, timeout=1)
    time.sleep(0.25)  # Esperar a que se establezca la conexión
except serial.SerialException as e:
    print(f"Error al abrir el puerto serial COM11: {e}")
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
    #"""Encuentra el keypoint más cercano al punto actual en el frame anterior."""
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
# Función para leer datos del sensor
def leer_sensor():
    global valor_leido, newtons
    try:
        puerto_serial.reset_input_buffer()
        # Enviar comando '0' para solicitar lectura única
        puerto_serial.write(b'0')
        # Leer respuesta del Arduino
        linea = puerto_serial.readline().decode('utf-8').strip()
        if linea:
            partes = linea.split()
            if len(partes) >= 4:
                valor_leido = float(partes[2])
                newtons = float(partes[4])
                print(f"Frame {frame_count}: Fuerza: {newtons:.2f} N")
                return True
    except serial.SerialException as e:
        print(f"Error al leer del sensor: {e}")
    return False


# Función para capturar el frame de referencia y seleccionar la ROI
def capture_reference_frame():
    global reference_frame, reference_keypoints, reference_descriptors, roi, prev_keypoints, 
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
    

    control_motor(MOTOR_FREQUENCY)
    leer_sensor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    # Guardar en Excel
    ws.append([timestamp, valor_leido, newtons, frame_count,
               last_valid_displacement, last_valid_dx, last_valid_dy])
    prev_keypoints = None
    return True
start_time=time.time()
# Capturar el frame de referencia y seleccionar la ROI inicial
if not capture_reference_frame():
    cap.release()
    cap2.release()
    cv2.destroyAllWindows()
    exit()
time_in = time.time()
time_paused = 0

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
                    dx_abs = abs(pt_curr[0] - pt_ref[0])
                    dy_abs = abs(pt_curr[1] - pt_ref[1])

                    # 2. Filtro entre frames consecutivos (si hay datos previos)
                    if prev_keypoints is not None:
                        prev_pt = find_closest_keypoint(pt_curr, prev_keypoints)
                        if prev_pt is not None:
                            dx_frame = pt_curr[0] - prev_pt[0]
                            dy_frame = pt_curr[1] - prev_pt[1]
                            if abs(dx_frame) > FRAME_TO_FRAME_THRESHOLDx or abs(dy_frame) > FRAME_TO_FRAME_THRESHOLDy:
                                continue #revisar si sería break

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
            
        if leer_sensor():
            #Leer datos del sensor ANTES(milisegundos) de guardar los frames
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            # Guardar en Excel
        ws.append([timestamp, valor_leido, newtons, 
                  average_displacement, average_dx, average_dy, frame_count])
            
        # Guardar frames como imágenes PNG (en lugar de usar VideoWriter)
        cv2.imwrite(f"frames_macro/frame_{frame_count:06d}.png", frame)
        cv2.imwrite(f"frames_micro/frame_{frame_count:06d}.png", frame2)
        frame_count += 1
        cv2.imshow('Camara meso', frame_with_roi)
        cv2.imshow('Camara micro', frame2_display)
        
    if paused:
        frame_paused = frame.copy()
        cv2.putText(frame_with_roi, "PAUSADO", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0, 0, 255), 2, cv2.LINE_AA)

        frame2_paused = frame2.copy()
        cv2.putText(frame2_paused, "PAUSADO", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow('Camara micro', frame2_paused)
        cv2.imshow('Camara meso', frame_paused)
      
        
    key = cv2.waitKey(1)
    if key & 0xFF == ord('p'):
        paused = not paused
        if paused:
            control_motor(None)
            control_motor(MOTOR_STOP_FREQUENCY)
            time_paused_in = time.time()
            print("Pausado - Motor detenido completamente - serial de lectura cerrado")
        else:
            try:
                puerto_serial.reset_input_buffer()
            except serial.SerialException as e:
                print(f"Error al reabrir el puerto serial: {e}")
            if not capture_reference_frame():
                break
            print("Continuando con nueva referencia. Motor iniciado.")
            time_paused_re = time.time() - time_paused_in
            time_paused += time_paused_re
            
    if key & 0xFF == ord('q'):
        control_motor(None)
        control_motor(MOTOR_STOP_FREQUENCY)
        print("Finalizado - Motor detenido completamente")
        break
        
# Guardar el archivo Excel
tictoc = time.time() - time_in - time_paused
print(f"Duración real:{tictoc:.4f}")
output_file = "deformation_RT.xlsx"
wb.save(output_file)
print(f"Datos guardados en {output_file}")

# Liberar recursos
cap.release()
cap2.release()
cv2.destroyAllWindows()

try:
    puerto_serial.close()
    puerto_serial2.close()
except serial.SerialException as e:
    print(f"Error al cerrar el puerto serial: {e}")

fpsout = frame_count / tictoc
print("Proceso completado. Para crear los videos ejecuta:")
print(f"ffmpeg -r {fpsout:.2f} -i frames_macro/frame_%06d.png -c:v libx264 -pix_fmt yuv420p -vf video_macro.mp4")
print(f"ffmpeg -r {fpsout:.2f} -i frames_micro/frame_%06d.png -c:v libx264 -pix_fmt yuv420p -vf video_micro.mp4")
