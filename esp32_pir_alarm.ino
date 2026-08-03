/*
  ESP32 PIR Motion Alarm with Telegram Notifications
  Copyright 2026 @nefariousjosiah
  ---------------------------------------------------
  Beginner-friendly security gadget:
  - PIR sensor watches for motion
  - Push button arms/disarms the system
  - LED shows status (slow blink = armed, off = disarmed, fast blink = ALARM)
  - Buzzer sounds when motion is detected while armed
  - A Telegram message is sent to your phone when the alarm triggers

  HARDWARE (see wiring diagram / README):
    PIR sensor OUT  -> GPIO 27
    Buzzer (+)      -> GPIO 26
    Status LED (+)  -> GPIO 25 (through 220ohm resistor)
    Arm/Disarm btn  -> GPIO 4  (other leg to GND, uses internal pull-up)

  LIBRARIES (install via Arduino IDE Library Manager):
    - UniversalTelegramBot   by Brian Lough / witnessmenow
    - ArduinoJson            (v6.x — required by UniversalTelegramBot)
  Board package:
    - "esp32" by Espressif Systems (install via Boards Manager)

  SETUP:
    1. Fill in WIFI_SSID / WIFI_PASSWORD below.
    2. Create a Telegram bot with @BotFather, paste the token into BOT_TOKEN.
    3. Message your new bot once, then get your chat ID from @userinfobot
       (or by visiting https://api.telegram.org/bot<TOKEN>/getUpdates).
    4. Paste your chat ID into CHAT_ID.
    5. Flash to the ESP32 and open Serial Monitor at 115200 baud to confirm.
*/

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <UniversalTelegramBot.h>

// ---------- USER SETTINGS ----------
const char* WIFI_SSID     = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* BOT_TOKEN     = "YOUR_TELEGRAM_BOT_TOKEN";
const char* CHAT_ID       = "YOUR_TELEGRAM_CHAT_ID";

// ---------- PIN ASSIGNMENTS ----------
const int PIR_PIN    = 27;
const int BUZZER_PIN = 26;
const int LED_PIN    = 25;
const int BUTTON_PIN = 4;

// ---------- TIMING SETTINGS ----------
const unsigned long ALERT_COOLDOWN_MS = 60000;  // min gap between Telegram alerts (60s)
const unsigned long ALARM_SOUND_MS    = 4000;   // how long buzzer sounds per trigger
const unsigned long DEBOUNCE_MS       = 250;    // button debounce window

// ---------- STATE ----------
bool armed = true;
bool lastButtonReading = HIGH;
unsigned long lastButtonChangeTime = 0;

bool alarmActive = false;
unsigned long alarmStartTime = 0;
unsigned long lastAlertSentTime = 0;

unsigned long lastStatusBlinkTime = 0;
bool statusLedState = false;

WiFiClientSecure secureClient;
UniversalTelegramBot bot(BOT_TOKEN, secureClient);

void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(400);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected, IP: " + WiFi.localIP().toString());
}

void sendTelegramAlert() {
  String msg = armed
    ? "Motion detected! Alarm triggered."
    : "Motion detected (system disarmed, FYI only).";
  bool ok = bot.sendMessage(CHAT_ID, msg, "");
  Serial.println(ok ? "Telegram alert sent." : "Failed to send Telegram alert.");
}

void handleButton() {
  bool reading = digitalRead(BUTTON_PIN);
  if (reading != lastButtonReading) {
    lastButtonChangeTime = millis();
  }
  if ((millis() - lastButtonChangeTime) > DEBOUNCE_MS) {
    // Button is wired to GND with internal pull-up, so LOW = pressed
    static bool handledThisPress = false;
    if (reading == LOW && !handledThisPress) {
      armed = !armed;
      handledThisPress = true;
      Serial.println(armed ? "System ARMED" : "System DISARMED");
      // stop any active alarm immediately when disarming
      if (!armed) {
        alarmActive = false;
        digitalWrite(BUZZER_PIN, LOW);
      }
    }
    if (reading == HIGH) {
      handledThisPress = false;
    }
  }
  lastButtonReading = reading;
}

void updateStatusLed() {
  if (alarmActive) {
    // fast blink during alarm
    if (millis() - lastStatusBlinkTime > 100) {
      lastStatusBlinkTime = millis();
      statusLedState = !statusLedState;
      digitalWrite(LED_PIN, statusLedState);
    }
  } else if (armed) {
    // slow blink when armed and idle
    if (millis() - lastStatusBlinkTime > 1000) {
      lastStatusBlinkTime = millis();
      statusLedState = !statusLedState;
      digitalWrite(LED_PIN, statusLedState);
    }
  } else {
    // disarmed: LED off
    digitalWrite(LED_PIN, LOW);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIR_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_PIN, LOW);

  connectWiFi();
  secureClient.setInsecure(); // skip cert validation (fine for personal bot use)

  Serial.println("PIR warming up (30s)...");
  delay(30000); // PIR sensors need a warm-up period to stabilize
  Serial.println("Ready.");
}

void loop() {
  handleButton();

  bool motionDetected = digitalRead(PIR_PIN) == HIGH;

  if (armed && motionDetected && !alarmActive) {
    alarmActive = true;
    alarmStartTime = millis();
    digitalWrite(BUZZER_PIN, HIGH);
    Serial.println("MOTION DETECTED - alarm on");

    if (millis() - lastAlertSentTime > ALERT_COOLDOWN_MS) {
      sendTelegramAlert();
      lastAlertSentTime = millis();
    }
  }

  if (alarmActive && (millis() - alarmStartTime > ALARM_SOUND_MS)) {
    alarmActive = false;
    digitalWrite(BUZZER_PIN, LOW);
  }

  updateStatusLed();
}
