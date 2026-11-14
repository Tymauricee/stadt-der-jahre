// ============================================================================
//  Stadt der Jahre / 年の街  –  MUROS Week Tokyo 2026, Meisei University
//
//  WS2812B-Panel 16x16. Jedes Jahr 1982–2024 = eine LED = ein 3D-gedruckter Turm.
//  Zeile = Jahrzehnt (vorne 1980er -> hinten 2020er), Spalte = Jahr im Jahrzehnt.
//  Hinterer Block: Japanisches Meer (JMA, Gebiet N2).
//  Vorderer Block: NW-europäischer Schelf inkl. Nordsee (Copernicus).
//  Farbe: Abweichung vom Mittel 1991–2020 (blau = kälter, rot = wärmer).
//  Ein Knopfdruck -> die Jahre laufen durch, beide Meere spielen je einen Ton.
//
//  Board: Freenove ESP32-WROOM (FNK0090), in der Arduino IDE "ESP32 Dev Module".
//  Bibliothek: FastLED. Treiber falls nötig: CH340.
//
//  EN: 16x16 WS2812B panel, one LED (= one 3D-printed tower) per year 1982–2024.
//  Back block: Sea of Japan, front block: NW European shelf. Colour = anomaly vs.
//  1991–2020. Button on GPIO 27 plays all years and streams them over USB serial
//  (115200 baud) to the exhibition page: "START", then "1982  JP -0.70  EU -0.31" ...
// ============================================================================

#include <FastLED.h>

// ---------- Pins ----------
// Alle benutzten Pins liegen auf EINER Seite des Boards (Seite mit 5V, GND, 25, 26, 27),
// damit nur diese Seite auf dem Steckbrett zugänglich sein muss.
#define PIN_LED     26      // grünes Kabel (DAT) des Panels, über 330-Ohm-Widerstand
#define PIN_BUTTON  27      // Taster zwischen GPIO 27 und GND
#define PIN_BUZZER  25      // optional: Piezo-Buzzer (+), anderes Bein an GND.
                            // In der Ausstellung kommt der Ton vom Laptop, der Pin bleibt dann frei.

// ---------- Panel ----------
#define W 16
#define H 16
#define NUM_LEDS (W * H)
// Ausrichtung (getestet): VORNE = Kante, an der LED 15 (rot) und 16 (blau) im Test
// leuchteten. Das Eingangskabel kommt dann LINKS raus. Der 3D-Druck kommt mit der
// Kerbe nach vorne darauf.
#define TEST_ORIENTATION 0
#define SERPENTINE  true    // Zickzack-Verdrahtung (bei flexiblen 16x16-Panels üblich)
#define FLIP_X      false
#define FLIP_Y      false
#define SWAP_XY     true    // Panel läuft in Spalten (getestet 10.11.)

// ---------- Einstellungen ----------
#define BRIGHTNESS    255   // volle Helligkeit
#define POWER_MA      900   // Stromgrenze über USB vom Laptop. Startet das Board beim Durchlauf neu -> 700.
                            // Mit eigenem 5-V-Netzteil (>= 3 A) für das Panel: 2500
#define MS_PER_YEAR   550   // Tempo pro Jahr (vorher 320 = zu schnell)
#define MS_LAST_DECADE 800  // 2020er langsamer -> Spannung zum Schluss
#define DECADE_PAUSE  500   // kurze Pause vor 1990, 2000, 2010, 2020
#define TONE_MS       150
#define SCALE_C       2.0f
#define N_YEARS       43    // 1982–2024
const int FIRST_YEAR = 1982;

// ---------- Daten: Abweichung in °C vom Mittel 1991–2020 ----------
// Japanisches Meer, Mitte (JMA areaF_SST.txt, Jahresmittel)
const float SST_JP[N_YEARS] = {
  -0.70f, -0.75f, -0.92f, -0.71f, -1.77f, -1.14f, -0.59f, -0.33f,  0.14f, -0.40f,  // 1982–1991
  -0.32f, -0.89f, -0.02f, -0.52f, -1.09f, -0.44f,  0.51f,  0.34f,  0.05f,  0.38f,  // 1992–2001
  -0.09f,  0.10f,  0.18f, -0.06f, -0.83f,  0.01f,  0.19f, -0.10f,  1.00f, -0.15f,  // 2002–2011
   0.17f,  0.11f, -0.06f, -0.47f,  0.47f,  0.66f, -0.16f,  0.63f,  0.83f,  1.37f,  // 2012–2021
   1.05f,  2.03f,  1.99f                                                             // 2022–2024
};
// NW-europäischer Schelf inkl. Nordsee (Copernicus OMI, Jahresmittel aus Monatswerten)
const float SST_EU[N_YEARS] = {
  -0.31f, -0.44f, -0.25f, -0.49f, -0.75f, -0.56f, -0.38f, -0.02f, -0.02f, -0.25f,  // 1982–1991
  -0.33f, -0.50f, -0.39f, -0.02f, -0.38f,  0.03f, -0.08f, -0.01f, -0.07f,  0.07f,  // 1992–2001
   0.16f,  0.29f,  0.16f,  0.11f,  0.28f,  0.32f,  0.17f,  0.12f, -0.03f, -0.06f,  // 2002–2011
  -0.09f, -0.12f,  0.37f, -0.15f,  0.11f,  0.12f, -0.03f,  0.12f,  0.06f,  0.09f,  // 2012–2021
   0.37f,  0.44f,  0.29f                                                             // 2022–2024
};

// ---------- Layout im Raster ----------
// Spalte = 3 + (Jahr % 10). Zeile: Japan 1980er = 7 ... 2020er = 3,
// Europa 1980er = 13 ... 2020er = 9.  Zeile 0 = hinten, Zeile 15 = vorne.
int colOf(int year)            { return 3 + (year % 10); }
int rowOf(int year, bool jp)   { int dec = (year - 1980) / 10; return (jp ? 3 : 9) + (4 - dec); }

CRGB leds[NUM_LEDS];
int hotJP[3], hotEU[3];

// (x, y) im Raster -> Nummer der LED auf dem Panel
int XY(int x, int y) {
  if (FLIP_X) x = W - 1 - x;
  if (FLIP_Y) y = H - 1 - y;
  if (SWAP_XY) { int t = x; x = y; y = t; }
  if (SERPENTINE && (y % 2 == 1)) x = W - 1 - x;
  return y * W + x;
}
int ledJP(int i) { int y = FIRST_YEAR + i; return XY(colOf(y), rowOf(y, true)); }
int ledEU(int i) { int y = FIRST_YEAR + i; return XY(colOf(y), rowOf(y, false)); }

CRGB colorFor(float a) {
  float t = constrain((a + SCALE_C) / (2 * SCALE_C), 0.0f, 1.0f);
  // satte Farben, normale Jahre nur gedämpftes Weiß -> Warm/Kalt springt mehr ins Auge
  const CRGB stops[5] = { CRGB(0, 30, 255), CRGB(30, 130, 255), CRGB(90, 90, 90),
                          CRGB(255, 80, 0), CRGB(255, 0, 0) };
  float pos = t * 4.0f;
  int i = min((int)pos, 3);
  return blend(stops[i], stops[i + 1], (uint8_t)((pos - i) * 255));
}

int freqFor(float a) {
  const int notes[11] = {220, 262, 294, 330, 392, 440, 523, 587, 659, 784, 880};
  float t = constrain((a + SCALE_C) / (2 * SCALE_C), 0.0f, 1.0f);
  return notes[(int)round(t * 10)];
}

void hottest3(const float* v, int out[3]) {
  out[0] = out[1] = out[2] = -1;
  for (int k = 0; k < 3; k++) {
    int best = -1;
    for (int i = 0; i < N_YEARS; i++) {
      if (i == out[0] || i == out[1]) continue;
      if (best < 0 || v[i] > v[best]) best = i;
    }
    out[k] = best;
  }
}

bool buttonPressed() {
  if (digitalRead(PIN_BUTTON) == HIGH) return false;
  delay(30);
  return digitalRead(PIN_BUTTON) == LOW;
}

void playTone(int freq, int ms) { tone(PIN_BUZZER, freq); delay(ms); noTone(PIN_BUZZER); }

// Lockmodus: langsame Lichtwelle über die Jahre, die drei wärmsten Jahre "atmen"
void attractFrame() {
  uint32_t t = millis();
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  for (int i = 0; i < N_YEARS; i++) {
    uint8_t b = 70 + scale8(sin8((uint8_t)((t / 12) - i * 10)), 185);
    CRGB c1 = colorFor(SST_JP[i]); c1.nscale8(b); leds[ledJP(i)] = c1;
    CRGB c2 = colorFor(SST_EU[i]); c2.nscale8(b); leds[ledEU(i)] = c2;
  }
  uint8_t pulse = beatsin8(14, 150, 255);
  for (int k = 0; k < 3; k++) {
    CRGB a = colorFor(SST_JP[hotJP[k]]); a.nscale8(pulse); leds[ledJP(hotJP[k])] = a;
    CRGB b = colorFor(SST_EU[hotEU[k]]); b.nscale8(pulse); leds[ledEU(hotEU[k])] = b;
  }
  FastLED.show();
}

// Ein Durchlauf 1982 -> 2024 nach Knopfdruck, endet automatisch
void playback() {
  Serial.println("START");                      // Laptop-Seite: Durchlauf beginnt
  // sanft ausblenden, dann kurz dunkel -> man merkt: jetzt geht's los
  for (int n = 0; n < 25; n++) { fadeToBlackBy(leds, NUM_LEDS, 30); FastLED.show(); delay(30); }
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
  delay(700);
  for (int i = 0; i < N_YEARS; i++) {
    int year = FIRST_YEAR + i;
    if (i > 0 && year % 10 == 0) delay(DECADE_PAUSE);   // neues Jahrzehnt = neue Reihe
    leds[ledJP(i)] = colorFor(SST_JP[i]);
    leds[ledEU(i)] = colorFor(SST_EU[i]);
    FastLED.show();
    Serial.printf("%d  JP %+.2f  EU %+.2f\n", FIRST_YEAR + i, SST_JP[i], SST_EU[i]);
    playTone(freqFor(SST_JP[i]), TONE_MS);      // erst Japan ...
    delay(20);
    playTone(freqFor(SST_EU[i]), TONE_MS);      // ... dann Europa
    int ms = (year >= 2020) ? MS_LAST_DECADE : MS_PER_YEAR;
    int rest = ms - 2 * TONE_MS - 20;
    if (rest > 0) delay(rest);
  }
  for (int n = 0; n < 2; n++) {                 // Finale: wärmste Jahre blinken
    for (int k = 0; k < 3; k++) { leds[ledJP(hotJP[k])] = CRGB::Black; leds[ledEU(hotEU[k])] = CRGB::Black; }
    FastLED.show(); delay(250);
    for (int k = 0; k < 3; k++) { leds[ledJP(hotJP[k])] = colorFor(SST_JP[hotJP[k]]); leds[ledEU(hotEU[k])] = colorFor(SST_EU[hotEU[k]]); }
    FastLED.show(); delay(250);
  }
  delay(4000);
  while (digitalRead(PIN_BUTTON) == LOW) delay(20);
}

// Ausrichtungstest: zeigt, wo LED 0 sitzt und wie die Reihen laufen
void orientationTest() {
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  leds[0]  = CRGB::Green;    // LED Nr. 0
  leds[1]  = CRGB::Yellow;   // LED Nr. 1
  leds[15] = CRGB::Red;      // LED Nr. 15 (Ende der ersten Reihe)
  leds[16] = CRGB::Blue;     // LED Nr. 16 (Anfang der zweiten Reihe)
  FastLED.show();
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  FastLED.addLeds<WS2812B, PIN_LED, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.setMaxPowerInVoltsAndMilliamps(5, POWER_MA);
  hottest3(SST_JP, hotJP);
  hottest3(SST_EU, hotEU);
  if (TEST_ORIENTATION) orientationTest();
}

void loop() {
  if (TEST_ORIENTATION) { delay(100); return; }
  if (buttonPressed()) playback();
  else attractFrame();
  delay(20);
}
