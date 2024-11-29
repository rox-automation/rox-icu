#include <Arduino.h>
#include <CANSAME5x.h>

CANSAME5x CAN;

const int LED_PIN = 13; // PA23 corresponds to Arduino pin 13

// Timing variables
unsigned long loopStart;
unsigned long counter = 0;
float maxLoopTime = 0;
float totalLoopTime = 0;
int loopCount = 0;

void setup()
{
  pinMode(LED_PIN, OUTPUT); // Set PA23 (pin 13) as output

  Serial.begin(115200);

  pinMode(PIN_CAN_STANDBY, OUTPUT);
  digitalWrite(PIN_CAN_STANDBY, false); // turn off STANDBY
  pinMode(PIN_CAN_BOOSTEN, OUTPUT);
  digitalWrite(PIN_CAN_BOOSTEN, true); // turn on booster

  // Initialize CAN bus
  if (!CAN.begin(500E3))
  { // 500kbps
    Serial.println("Starting CAN failed!");
    while (1)
      ;
  }

  // Start timing for first loop
  loopStart = micros();
}

void loop()
{
  // Record start time of this loop
  unsigned long currentLoopStart = micros();

  // Calculate previous loop duration (convert to ms)
  float loopTime = (currentLoopStart - loopStart) / 1000.0;

  // Update timing statistics
  maxLoopTime = max(maxLoopTime, loopTime);
  totalLoopTime += loopTime;
  loopCount++;

  // Store start time for next iteration
  loopStart = currentLoopStart;

  // Increment counter and send via CAN
  counter++;
  counter &= 0xFFFFFFFF;

  byte data[4];
  data[0] = counter & 0xFF;
  data[1] = (counter >> 8) & 0xFF;
  data[2] = (counter >> 16) & 0xFF;
  data[3] = (counter >> 24) & 0xFF;

  CAN.beginPacket(0x01);
  CAN.write(data, 4);
  CAN.endPacket();

  // Print statistics every 1000 loops
  if (loopCount >= 1000)
  {
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));

    float avgLoopTime = totalLoopTime / 1000.0;
    unsigned long uptimeSeconds = millis() / 1000;

    Serial.print("Stats - Avg: ");
    Serial.print(avgLoopTime, 3);
    Serial.print(" ms, Max: ");
    Serial.print(maxLoopTime, 3);
    Serial.print(" ms, Counter: ");
    Serial.print(counter);
    Serial.print(", Uptime: ");
    Serial.print(uptimeSeconds);
    Serial.println(" s");

    // Reset statistics
    maxLoopTime = 0;
    totalLoopTime = 0;
    loopCount = 0;
  }

  // Use microsecond delay instead of millisecond
  delayMicroseconds(100); // 100 microseconds = 0.1 milliseconds
}
