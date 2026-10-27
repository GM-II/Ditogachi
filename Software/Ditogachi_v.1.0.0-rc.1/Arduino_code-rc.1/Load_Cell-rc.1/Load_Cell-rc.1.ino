/*   
  Load_Cell-rc.1.ino
  This code belong to the Ditogachi's project by the Grupo de Microscopia, Intrumentación e Innovación GM-II
  For more info please visit the group GitHub: https://github.com/GM-II

  It's the rc code who allow us to sense and get the data from the load cell 
  and also allow to comunicate with the main python code for a centralized and synchronised
  management of the whole system.

  Note: That the code used in the type 1 bovine collagen essay.
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
//mirar señal para autorización de sensado desde python copy as Control Potro
void loop() {
  // Promedia múltiples lecturas
  float suma = 0;
  for (int i = 0; i < numSamples; i++) {
    suma += analogRead(sensorPin);
    delay(1); // Pequeña pausa entre lecturas
  }
  sensorValue = suma / numSamples;

  // Convierte a voltaje (si la referencia es 5V)
  float Newtons = sensorValue * (5.0 / 1023.0)*97.54; //(5.0 / 1023.0)*1.96; valor para la celda de 1kg

  Serial.print("Valor leído: ");
  Serial.print(sensorValue);
  Serial.print("  Newtons: ");
  Serial.println(Newtons, 5); // 3 decimales
  delay(250);
}
