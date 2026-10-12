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
RESOLUCION =  (1280, 720)

# Configuración del motor
MOTOR_FREQUENCY = 200  # Frecuencia inicial del motor en Hz
MOTOR_STOP_FREQUENCY = 0  # Frecuencia para detener el motor

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

#VERIFICAR (solo para seguridad)
actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Resolución cámara 1: {actual_width}x{actual_height}")

actual_width2 = int(cap2.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_height2 = int(cap2.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Resolución cámara 2: {actual_width2}x{actual_height2}")

# Crear directorios para frames
os.makedirs('frames_macro_TR', exist_ok=True)
os.makedirs('frames_micro_TR', exist_ok=True)

# Variables para almacenar los últimos desplazamientos válidos
frame_count = 0
valor_leido = 0.0
newtons = 0.0

# Crear un archivo Excel para guardar los datos
wb = Workbook()
ws = wb.active
ws.title = "Tensión"
# Encabezados actualizados con todos los valores
ws.append(["Timestamp", "Frame", "Valor leído", "Newtons"])  

# Variable para controlar la pausa
paused = False

# Configura el puerto serial (ajusta el puerto y el baud rate según tu configuración)
try:
    puerto_serial2 = serial.Serial('COM3', 115200, timeout=1)# Cambia 'COMX' por el puerto correcto
    # Esperar a que se establezca la conexión
    time.sleep(0.5)
except serial.SerialException as e:
    print(f"Error al abrir el puerto serial: {e}")
    exit()
############################
try:
    puerto_serial = serial.Serial('COM11', 115200, timeout=1)
    time.sleep(0.5)  # Esperar a que se establezca la conexión
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
def Start_codex():
    global puerto_serial, roi
    ret, frame = cap.read()
    if not ret:
        print("Error: No se pudo capturar el frame de referencia.")
        return False

    roi = cv2.selectROI("Selecciona la ROI", frame, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow("Selecciona la ROI")
    
    print("Secuencia iniciada.")    
    control_motor(MOTOR_FREQUENCY)
    leer_sensor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    # Guardar en Excel
    ws.append([timestamp, frame_count, valor_leido, newtons])
    return True
time_paused = 0
# Iniciar la secuencia
Start_codex()

start_time = time.time()
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
        
    if not paused:
        # Leer datos del sensor ANTES(milisegundos) de guardar los frames
        if leer_sensor():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            # Guardar en Excel
            ws.append([timestamp, frame_count, valor_leido, newtons])
        
        # Guardar frames como imágenes PNG 
        cv2.imwrite(f"frames_macro_TR/frame_{frame_count:06d}.png", frame)
        cv2.imwrite(f"frames_micro_TR/frame_{frame_count:06d}.png", frame2)
        frame_count += 1
        
    # Mostrar frames
    if paused:
        frame_paused = frame.copy()
        cv2.putText(frame_paused, "PAUSADO", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow('Camara meso', frame_paused)
        
        frame2_paused = frame2.copy()
        cv2.putText(frame2_paused, "PAUSADO", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow('Camara micro', frame2_paused)
    else:
        cv2.imshow('Camara meso', frame_display)
        cv2.imshow('Camara micro', frame2_display)

    key = cv2.waitKey(1)
    if key & 0xFF == ord('p'):
        paused = not paused
        if paused:
            control_motor(None)
            control_motor(MOTOR_STOP_FREQUENCY)
            time_paused_in = time.time()
            try:
                puerto_serial.close()
            except serial.SerialException as e:
                print(f"Error al cerrar el puerto serial: {e}")
            print("Pausado - Motor detenido completamente - serial de lectura cerrado")
        else:
            #cv2.destroyWindow('Camara pausa')
            try:
                puerto_serial.open()
                puerto_serial.reset_input_buffer()
            except serial.SerialException as e:
                print(f"Error al reabrir el puerto serial: {e}")
            if not Start_codex():
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
print(f"Duración real: {tictoc:.4f}")
output_file = "analisis_tensionFF-TR.xlsx"
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
print(f"ffmpeg -r {fpsout:.2f} -i frames_macro_TR/frame_%06d.png -c:v libx264 -pix_fmt yuv420p -vf video_macro.mp4")
print(f"ffmpeg -r {fpsout:.2f} -i frames_micro_TR/frame_%06d.png -c:v libx264 -pix_fmt yuv420p -vf video_micro.mp4")
