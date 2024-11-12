#include <Arduino.h>

// Define PA23 and PA27 for clarity
const int LED_PIN = 13;      // PA23 corresponds to Arduino pin 13
const int DELAY_TIME_US = 5; // 100 kHz for PA27

void setup()
{
  pinMode(LED_PIN, OUTPUT); // Set PA23 (pin 13) as output
  // Set PA27 as output
  PORT->Group[0].DIRSET.reg = (1 << 27);
}

void loop()
{
  // Toggle PA27 at high frequency
  PORT->Group[0].OUTSET.reg = (1 << 27);
  delayMicroseconds(DELAY_TIME_US);
  PORT->Group[0].OUTCLR.reg = (1 << 27);
  delayMicroseconds(DELAY_TIME_US);

  // Toggle PA23 at a divided frequency
  static int counter = 0;
  counter++;

  // Divide the frequency of PA27 by 20000 (for example)
  if (counter >= 20000)
  {
    digitalWrite(LED_PIN, !digitalRead(LED_PIN)); // Toggle PA23
    counter = 0;                                  // Reset counter
  }
}
