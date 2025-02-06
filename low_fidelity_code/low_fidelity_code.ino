#define LED_PIN 8
#define SENSOR_PIN A5

void setup() {
Serial.begin(9600);
pinMode(LED_PIN, OUTPUT); 
pinMode(SENSOR_PIN, INPUT);
}

void loop() {
digitalWrite(LED_PIN, LOW);
int sensorValue = analogRead(SENSOR_PIN);
Serial.println(sensorValue);
delay(10);
}