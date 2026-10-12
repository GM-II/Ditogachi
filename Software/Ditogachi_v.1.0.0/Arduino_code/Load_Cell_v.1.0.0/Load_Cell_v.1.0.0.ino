const int sensorPin = A0;   // Pin analógico
const int numSamples = 50; // Número de muestras para promediar
float sensorValue = 0;      // Almacenará el valor final

void setup() {
  Serial.begin(115200);
  analogReference(DEFAULT); // Usa referencia de voltaje de 5V
}

void loop() {
  // Verificar si hay comandos desde Python
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    if (command == '0') {
      // Lectura única al tener '0'
      readAndSendSensorData();
    } 
    }
  }
}

// Función para leer y enviar datos del sensor
void readAndSendSensorData() {
  // Promedia múltiples lecturas
  float suma = 0;
  for (int i = 0; i < numSamples; i++) {
    suma += analogRead(sensorPin);
    delay(1); // Pequeña pausa entre lecturas
  }
  sensorValue = suma / numSamples;

  // Convierte a voltaje y luego a Newtons
  float Newtons = sensorValue * (5.0 / 1023.0) * 97.54;

  // Enviar datos por serial
  Serial.print("Valor leído: ");
  Serial.print(sensorValue);
  Serial.print("  Newtons: ");
  Serial.println(Newtons, 5);
}