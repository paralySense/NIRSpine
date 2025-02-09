#define LED_PINBLUE 5
#define LED_PINRED 8
#define SENSOR_PIN A5

void setup() {
Serial.begin(9600);
pinMode(LED_PINBLUE, OUTPUT); 
pinMode(LED_PINRED, OUTPUT); 
pinMode(SENSOR_PIN, INPUT);

Serial.println("Time, Sensor Value");
}

void loop() {
digitalWrite(LED_PINBLUE, HIGH);
digitalWrite(LED_PINRED, HIGH);
int sensorValue = analogRead(SENSOR_PIN);
//float time = millis();
// Serial.print(millis());
// Serial.print(",");
Serial.println(sensorValue);
delay(50);
}