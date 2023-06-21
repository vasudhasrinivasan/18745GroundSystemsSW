#include <WiFi.h>


void setup() {
  Serial.begin(115200);
  // put your setup code here, to run once:
  WiFi.begin("CMU-DEVICE");
}

void loop() {
  // put your main code here, to run repeatedly:
  while (WiFi.status () != WL_CONNECTED){
    delay(500);
    Serial.print('.');
  }
  Serial.print("Connected!\n");
}
