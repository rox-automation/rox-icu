/*
 * Based on Adafruit Feather M4 CAN Sender Example
 */

#include <CANSAME5x.h>

CANSAME5x CAN;

long counter = 0; // Changed from int to long
const int scopePin = 5;
const int loopDelay = 1; // Constant for loop delay in microseconds
const int sendInterval = 10000; // Constant for the number of loops between CAN packet sends

void setup() {

  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(scopePin, OUTPUT);

  Serial.begin(115200);
  while (!Serial) delay(10);

  Serial.println("CAN Sender");

  pinMode(PIN_CAN_STANDBY, OUTPUT);
  digitalWrite(PIN_CAN_STANDBY, false); // turn off STANDBY
  pinMode(PIN_CAN_BOOSTEN, OUTPUT);
  digitalWrite(PIN_CAN_BOOSTEN, true); // turn on booster

  // start the CAN bus at 250 kbps
  if (!CAN.begin(500000)) {
    Serial.println("Starting CAN failed!");
    while (1) delay(10);
  }
  Serial.println("Starting CAN!");
}

void loop() {
  // Toggle the scope pin and LED
  digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  digitalWrite(scopePin, !digitalRead(scopePin));

  // Increment the counter
  counter++;

  // Send CAN packet every 'sendInterval' iterations
  if (counter % sendInterval == 0) {
    // Break down the long counter into bytes and send them
    CAN.beginPacket(0x12);
    CAN.write((byte)(counter >> 24)); // Send the most significant byte
    CAN.write((byte)(counter >> 16));
    CAN.write((byte)(counter >> 8));
    CAN.write((byte)(counter));       // Send the least significant byte
    CAN.endPacket();
  }

  delayMicroseconds(loopDelay); // Delay in microseconds
}
