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
