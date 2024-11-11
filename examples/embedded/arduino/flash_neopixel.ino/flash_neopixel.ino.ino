#include <Adafruit_NeoPixel.h>

Adafruit_NeoPixel strip(1, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);

// Define colors: Green, Blue, Red
const uint32_t colors[] = {0x00FF00, 0x0000FF, 0xFF0000};
const int numColors = sizeof(colors) / sizeof(colors[0]);

void setup() {
  Serial.begin(115200);

  Serial.print("Running neopixel demo ");

  strip.begin();
  strip.setBrightness(50);
  strip.show();  // Initialize all pixels to 'off'
}

void setColor(uint32_t color) {
  strip.setPixelColor(0, color);
  strip.show();
  delay(200);
}

void loop() {
  for (int i = 0; i < numColors; i++) {
    setColor(colors[i]);
  }
}
