/*   
  Control_Motor_v.1.0.0.ino
  This code belong to the Ditogachi's project by the Grupo de Microscopia, Intrumentación e Innovación GM-II
  For more info please visit the group GitHub: https://github.com/GM-II

  It's the code who allow us to control the PWM that is given to the motor driver
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