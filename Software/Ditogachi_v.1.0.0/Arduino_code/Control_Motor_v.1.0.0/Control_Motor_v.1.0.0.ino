// Definir el pin donde se generará el pulso
const int pinPulso = 9;  // Pin 9 es válido en Arduino Uno
// Variable para almacenar la frecuencia deseada (en Hz)
int frecuencia = 0;  // Frecuencia inicial
// Variable para almacenar el período del pulso (en microsegundos)
unsigned long periodo;

void setup() {
  // Configurar el pin como salida
  pinMode(pinPulso, OUTPUT);
  digitalWrite(pinPulso, LOW);
  // Iniciar la comunicación serial
  Serial.begin(115200);
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    
    if (input == "STOP") {
      // Detener completamente los pulsos
      digitalWrite(pinPulso, LOW);
    } else {
      // Procesar como frecuencia
      frecuencia = input.toInt();
      periodo = 1000000 / frecuencia;
    }
  }

  if (frecuencia > 0) {  // Solo generar pulsos si frecuencia > 0
    digitalWrite(pinPulso, HIGH);
    delayMicroseconds(periodo / 2);
    digitalWrite(pinPulso, LOW);
    delayMicroseconds(periodo / 2);
  } else {
    digitalWrite(pinPulso, LOW);
    }
}