/*   
  Load_Cell_v.1.0.0.ino
  This code belong to the Ditogachi's project by the Grupo de Microscopia, Intrumentación e Innovación GM-II
  For more info please visit the group GitHub: https://github.com/GM-II

  It's the code who allow us to sense and get the data from the load cell 
  and also allow to comunicate with the main python code for a centralized and synchronised
  management of the whole system.

  Copyright 2026 Grupo de Microscopía, Instrumentación e Innovación GM-II (S. Rosas, S. Triviño, C. Garzón)

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License. */
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
  float Newtons = sensorValue * (5.0 / 1023.0) * 97.54; //Cambiar conversión para celda de 1kg

  // Enviar datos por serial
  Serial.print("Valor leído: ");
  Serial.print(sensorValue);
  Serial.print("  Newtons: ");
  Serial.println(Newtons, 5);
}