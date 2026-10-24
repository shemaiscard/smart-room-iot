// Wemos D1 MQTT Smart Home Kit Integration Code
// Tailored for Wemos D1 R1/R2 and ESP8266 based boards

#include <ESP8266WiFi.h>
#include <WiFiClientSecureBearSSL.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Adafruit_NeoPixel.h>
#include <Servo.h>
#include <time.h>
#include "DHT.h"

// ==================== CONFIGURATION ====================
// Wi-Fi, broker and signing key live in secrets.h (not in Git).
// Copy secrets.example.h to secrets.h and fill it in before uploading.
#include "secrets.h"

// Unique client identifier prefix
const char* client_id_prefix = "WemosSmartHome-";

// Messages older or newer than this (vs. the NTP clock) are rejected
const unsigned long long MAX_SKEW_MS = 30000ULL;
// ========================================================

// Root certificate of broker.hivemq.com (Amazon Root CA 1, valid until 2038).
// Replace it if you move to a broker with a different certificate authority.
static const char BROKER_CA[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
MIIDQTCCAimgAwIBAgITBmyfz5m/jAo54vB4ikPmljZbyjANBgkqhkiG9w0BAQsF
ADA5MQswCQYDVQQGEwJVUzEPMA0GA1UEChMGQW1hem9uMRkwFwYDVQQDExBBbWF6
b24gUm9vdCBDQSAxMB4XDTE1MDUyNjAwMDAwMFoXDTM4MDExNzAwMDAwMFowOTEL
MAkGA1UEBhMCVVMxDzANBgNVBAoTBkFtYXpvbjEZMBcGA1UEAxMQQW1hem9uIFJv
b3QgQ0EgMTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALJ4gHHKeNXj
ca9HgFB0fW7Y14h29Jlo91ghYPl0hAEvrAIthtOgQ3pOsqTQNroBvo3bSMgHFzZM
9O6II8c+6zf1tRn4SWiw3te5djgdYZ6k/oI2peVKVuRF4fn9tBb6dNqcmzU5L/qw
IFAGbHrQgLKm+a/sRxmPUDgH3KKHOVj4utWp+UhnMJbulHheb4mjUcAwhmahRWa6
VOujw5H5SNz/0egwLX0tdHA114gk957EWW67c4cX8jJGKLhD+rcdqsq08p8kDi1L
93FcXmn/6pUCyziKrlA4b9v7LWIbxcceVOF34GfID5yHI9Y/QCB/IIDEgEw+OyQm
jgSubJrIqg0CAwEAAaNCMEAwDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8EBAMC
AYYwHQYDVR0OBBYEFIQYzIU07LwMlJQuCFmcx7IQTgoIMA0GCSqGSIb3DQEBCwUA
A4IBAQCY8jdaQZChGsV2USggNiMOruYou6r4lK5IpDB/G/wkjUu0yKGX9rbxenDI
U5PMCCjjmCXPI6T53iHTfIUJrU6adTrCC2qJeHZERxhlbI1Bjjt/msv0tadQ1wUs
N+gDS63pYaACbvXy8MWy7Vu33PqUXHeeE6V/Uq2V8viTO96LXFvKWlJbYK8U90vv
o/ufQJVtMVT8QtPHRh8jrdkPSHCa2XV4cdFyQzR1bldZwgJcJmApzyMZFo6IQ6XU
5MsI+yMRQ+hDKXJioaldXgjUkK642M4UwtBV8ob2xJNDd2ZhwLnoQdeXeGADbkpy
rqXRfboQnoZsG4q5WTP468SQvvG5
-----END CERTIFICATE-----
)EOF";

// ==================== PIN DEFINITIONS ====================
// Supports both "Generic ESP8266 Module" and specific board profiles (LOLIN D1 R1/R2)
#ifndef D0
#define D0   3
#define D1   1
#define D2   16
#define D3   5
#define D4   4
#define D5   14
#define D6   12
#define D7   13
#define D8   0
#define D9   2
#define D10  15
#define D11  13
#define D12  12
#define D13  14
#define D14  4
#define D15  5
#endif

#define DHTPIN       D8           // Temp & Humidity Sensor (Physical pin 8)
#define DHTTYPE      DHT11        // Use DHT22 here for 0.1 degree / 0.1 % resolution
#define RGB_PIN      D6           // Neopixel RGB LED (Physical pin 6)
#define PIEZO_PIN    D7           // Piezo Buzzer (Physical pin 7)
#define IR_PIN       D9           // IR Sensor (Physical pin 9)
#define FAN_PIN      D11          // Cooling Fan (Physical pin 11)
#define SERVO_PIN    D13          // Door Servo Motor (Physical pin 13)
// =========================================================

// Initialize modules
LiquidCrystal_I2C lcd(0x27, 16, 2); // default address 0x27 (some LCDs use 0x3F)
Adafruit_NeoPixel RGB_LED(3, RGB_PIN, NEO_GRB + NEO_KHZ800);
Servo doorServo;
DHT dht(DHTPIN, DHTTYPE);

#if MQTT_USE_TLS
BearSSL::WiFiClientSecure espClient;
BearSSL::X509List brokerCA(BROKER_CA);
#else
WiFiClient espClient;
#endif
PubSubClient client(espClient);

// States and variables
bool capsMode = false;      // Security / Intruder Alarm mode
bool fanAutoMode = true;    // True: Fan turns on automatically based on temp. False: manual MQTT control.
int tones[] = { 261, 523 };  // Warning alarm tones
unsigned long lastPublishTime = 0;
const unsigned long publishInterval = 10000; // Publish telemetry every 10 seconds
unsigned long lastReconnectAttempt = 0;
const unsigned long reconnectInterval = 5000;
unsigned long long lastCommandTs = 0;  // newest accepted command (replay protection)
unsigned long long lastSentTs = 0;     // keeps our own timestamps strictly increasing

// Alarm runs as a small state machine so the main loop keeps serving MQTT:
// 10 steps of 300 ms, alternating red/high tone and blue/low tone.
bool alarmActive = false;
int alarmStep = 0;
unsigned long alarmStepAt = 0;
const int ALARM_STEPS = 10;
const unsigned long ALARM_STEP_MS = 300;

// MQTT Topics (aligned with Streamlit app; TOPIC_BASE may be set in secrets.h)
#ifndef TOPIC_BASE
#define TOPIC_BASE "giscard/smart_room"
#endif
const char* TOPIC_CONTROL    = TOPIC_BASE "/control"; // Subscribed control topic (device:state)
const char* TOPIC_STATUS     = TOPIC_BASE "/status";  // Retained: signed "online", or "offline" (last will)
const char* TOPIC_TEMP       = TOPIC_BASE "/temp";    // Telemetry output: temperature
const char* TOPIC_HUMID      = TOPIC_BASE "/hum";     // Telemetry output: humidity
const char* TOPIC_ALARM      = TOPIC_BASE "/alarm";   // Alarm events output

// ==================== MESSAGE SIGNING ====================
// Same format as secure_msg.py:
//   <body>|<timestamp ms>|<hex HMAC-SHA256(key, "<topic>|<body>|<timestamp ms>")>

String u64ToString(unsigned long long v) {
  char buf[21];
  int i = 20;
  buf[i] = '\0';
  do { buf[--i] = '0' + (v % 10); v /= 10; } while (v > 0);
  return String(&buf[i]);
}

bool clockIsSet() {
  return time(nullptr) > 1700000000;  // after Nov 2023: NTP has answered
}

unsigned long long nowMs() {
  return (unsigned long long)time(nullptr) * 1000ULL + (millis() % 1000);
}

String hmacHex(const String& text) {
  br_hmac_key_context kc;
  br_hmac_context hc;
  uint8_t out[32];
  br_hmac_key_init(&kc, &br_sha256_vtable, SMART_ROOM_KEY, strlen(SMART_ROOM_KEY));
  br_hmac_init(&hc, &kc, 0);
  br_hmac_update(&hc, text.c_str(), text.length());
  br_hmac_out(&hc, out);
  static const char hex[] = "0123456789abcdef";
  String s;
  s.reserve(64);
  for (int i = 0; i < 32; i++) { s += hex[out[i] >> 4]; s += hex[out[i] & 15]; }
  return s;
}

// Compare without stopping at the first difference (no timing leak)
bool equalsConstTime(const String& a, const String& b) {
  if (a.length() != b.length()) return false;
  uint8_t diff = 0;
  for (unsigned int i = 0; i < a.length(); i++) diff |= a[i] ^ b[i];
  return diff == 0;
}

String signMessage(const char* topic, const String& body) {
  unsigned long long ts = nowMs();
  if (ts <= lastSentTs) ts = lastSentTs + 1;
  lastSentTs = ts;
  String tsStr = u64ToString(ts);
  return body + "|" + tsStr + "|" + hmacHex(String(topic) + "|" + body + "|" + tsStr);
}

bool publishSigned(const char* topic, const String& body, bool retained = false) {
  if (!client.connected()) return false;
  return client.publish(topic, signMessage(topic, body).c_str(), retained);
}

// Returns true and fills body if the message is authentic, fresh and newer
// than the last accepted command.
bool verifyCommand(const char* topic, const String& payload, String& body) {
  int p2 = payload.lastIndexOf('|');
  if (p2 < 0) return false;
  int p1 = payload.lastIndexOf('|', p2 - 1);
  if (p1 < 0) return false;
  body = payload.substring(0, p1);
  String tsStr = payload.substring(p1 + 1, p2);
  String mac = payload.substring(p2 + 1);
  if (!equalsConstTime(mac, hmacHex(String(topic) + "|" + body + "|" + tsStr))) return false;
  unsigned long long ts = strtoull(tsStr.c_str(), nullptr, 10);
  unsigned long long now = nowMs();
  unsigned long long skew = ts > now ? ts - now : now - ts;
  if (skew > MAX_SKEW_MS) return false;
  if (ts <= lastCommandTs) return false;  // replayed or out of order
  lastCommandTs = ts;
  return true;
}
// =========================================================

void setup_wifi() {
  delay(10);
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(WIFI_SSID);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Connecting Wi-Fi");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int retry = 0;
  while (WiFi.status() != WL_CONNECTED && retry < 30) {
    delay(500);
    Serial.print(".");
    lcd.setCursor(retry % 16, 1);
    lcd.print(".");
    retry++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Wi-Fi Connected");
    lcd.setCursor(0, 1);
    lcd.print(WiFi.localIP().toString());
  } else {
    Serial.println("\nWi-Fi connection failed. Running offline mode.");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Wi-Fi Failed");
    lcd.setCursor(0, 1);
    lcd.print("Running Offline");
  }
  delay(1500);
}

// The clock is needed to check the broker's certificate and to timestamp
// signed messages.
void sync_clock() {
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  Serial.print("Waiting for NTP time");
  for (int i = 0; i < 40 && !clockIsSet(); i++) {
    delay(250);
    Serial.print(".");
  }
  Serial.println(clockIsSet() ? " done" : " failed (will keep trying)");
}

void setLEDColor(uint8_t r, uint8_t g, uint8_t b) {
  for (int i = 0; i < 3; i++) {
    RGB_LED.setPixelColor(i, r, g, b);
  }
  RGB_LED.show();
}

// Start the alarm: publish the event, then flash and beep from loop()
void triggerIntruderAlert() {
  Serial.println("INTRUSION DETECTED! Triggering Alarm.");
  publishSigned(TOPIC_ALARM, "INTRUSION DETECTED!");

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("!!! EMERGENCY !!!");
  lcd.setCursor(0, 1);
  lcd.print("INTRUDER DETECTED");

  alarmActive = true;
  alarmStep = 0;
  alarmStepAt = millis();
}

void stopAlarm() {
  alarmActive = false;
  noTone(PIEZO_PIN);
  setLEDColor(0, 0, 0);
  lcd.clear();
}

// One non-blocking step of the siren: red + high pitch, then blue + low pitch
void updateAlarm() {
  if (!alarmActive || millis() < alarmStepAt) return;
  if (alarmStep >= ALARM_STEPS) {
    stopAlarm();
    return;
  }
  if (alarmStep % 2 == 0) {
    setLEDColor(255, 0, 0);
    tone(PIEZO_PIN, tones[1]);
  } else {
    setLEDColor(0, 0, 255);
    tone(PIEZO_PIN, tones[0]);
  }
  alarmStep++;
  alarmStepAt = millis() + ALARM_STEP_MS;
}

void handleCommand(String message) {
  int colonIndex = message.indexOf(':');
  if (colonIndex <= 0) return;
  String device = message.substring(0, colonIndex);
  String state = message.substring(colonIndex + 1);

  device.toUpperCase();
  state.toUpperCase();

  if (device == "LIGHT") {
    if (state == "ON" || state == "WHITE") {
      setLEDColor(255, 255, 255);
      Serial.println("Light turned ON (White)");
    } else if (state == "OFF") {
      setLEDColor(0, 0, 0);
      Serial.println("Light turned OFF");
    } else if (state == "RED") {
      setLEDColor(255, 0, 0);
      Serial.println("Light turned RED");
    } else if (state == "GREEN") {
      setLEDColor(0, 255, 0);
      Serial.println("Light turned GREEN");
    } else if (state == "BLUE") {
      setLEDColor(0, 0, 255);
      Serial.println("Light turned BLUE");
    } else if (state == "YELLOW") {
      setLEDColor(255, 255, 0);
      Serial.println("Light turned YELLOW");
    } else if (state == "ORANGE") {
      setLEDColor(255, 128, 0);
      Serial.println("Light turned ORANGE");
    }
  }
  else if (device == "FAN") {
    if (state == "ON") {
      fanAutoMode = false;
      analogWrite(FAN_PIN, 255);
      Serial.println("Fan turned ON manually");
    } else if (state == "OFF") {
      fanAutoMode = false;
      analogWrite(FAN_PIN, 0);
      Serial.println("Fan turned OFF manually");
    } else if (state == "AUTO") {
      fanAutoMode = true;
      Serial.println("Fan set to AUTO mode");
    }
  }
  else if (device == "DOOR") {
    if (state == "UNLOCK") {
      doorServo.write(90);
      Serial.println("Door set to UNLOCKED (Open)");
    } else if (state == "LOCK") {
      doorServo.write(180);
      Serial.println("Door set to LOCKED (Closed)");
    }
  }
  else if (device == "CAPS" || device == "SECURITY") {
    if (state == "ON" || state == "ARM") {
      capsMode = true;
      Serial.println("Security Caps Mode: ARMED");
    } else if (state == "OFF" || state == "DISARM") {
      capsMode = false;
      Serial.println("Security Caps Mode: DISARMED");
      if (alarmActive) stopAlarm();
    }
  }
}

// Handles incoming MQTT messages: only signed, fresh commands are executed
void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  message.trim();

  if (String(topic) != TOPIC_CONTROL) return;

  String body;
  if (!verifyCommand(topic, message, body)) {
    Serial.println("Rejected unsigned, stale or replayed command");
    return;
  }
  Serial.println(body);
  handleCommand(body);
}

// One connection attempt; loop() calls it again every 5 s while offline
bool reconnect() {
  Serial.print("Attempting MQTT connection...");
  String clientId = client_id_prefix + String(random(0xffff), HEX);
  const char* user = strlen(MQTT_USER) ? MQTT_USER : nullptr;
  const char* pass = strlen(MQTT_PASS) ? MQTT_PASS : nullptr;

  // Last will: the broker marks the board offline if it vanishes
  if (client.connect(clientId.c_str(), user, pass, TOPIC_STATUS, 1, true, "offline")) {
    Serial.println("Connected to MQTT Broker!");
    publishSigned(TOPIC_STATUS, "online", true);

    // Subscribe to control topic (QoS 1: the broker retries until we acknowledge)
    client.subscribe(TOPIC_CONTROL, 1);
    return true;
  }
  Serial.print("failed, rc=");
  Serial.print(client.state());
#if MQTT_USE_TLS
  char err[80];
  espClient.getLastSSLError(err, sizeof(err));
  Serial.print(" tls=");
  Serial.print(err);
#endif
  Serial.println(" Retrying in 5 seconds...");
  return false;
}

void setup() {
  Serial.begin(115200);

  // Initialize LCD
  Wire.begin(4, 5); // Force SDA=GPIO 4, SCL=GPIO 5 for Wemos D1 I2C
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Initializing...");

  // Initialize actuators
  RGB_LED.begin();
  setLEDColor(0, 0, 0);

  pinMode(PIEZO_PIN, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);
  pinMode(IR_PIN, INPUT_PULLUP);

  doorServo.attach(SERVO_PIN);
  doorServo.write(180); // Default closed state

  dht.begin();

  setup_wifi();
  if (WiFi.status() == WL_CONNECTED) sync_clock();

#if MQTT_USE_TLS
  espClient.setTrustAnchors(&brokerCA);
  espClient.setBufferSizes(16384, 512); // full receive buffer: the broker does not negotiate smaller records
#endif
  client.setServer(MQTT_HOST, MQTT_PORT);
  client.setCallback(callback);
}

void loop() {
  // MQTT loop: never blocks, so the alarm and fan keep working while offline
  if (WiFi.status() == WL_CONNECTED && clockIsSet()) {
    if (!client.connected()) {
      unsigned long now = millis();
      if (lastReconnectAttempt == 0 || now - lastReconnectAttempt >= reconnectInterval) {
        lastReconnectAttempt = now;
        if (reconnect()) lastReconnectAttempt = 0;
      }
    } else {
      client.loop();
    }
  }

  // Security mode: check IR sensor (a new alert starts after the current one ends)
  if (capsMode && !alarmActive && digitalRead(IR_PIN) == LOW) {
    triggerIntruderAlert();
  }
  updateAlarm();

  // Telemetry publish and LCD display updates
  unsigned long currentMillis = millis();
  if (currentMillis - lastPublishTime >= publishInterval) {
    lastPublishTime = currentMillis;

    float hum = dht.readHumidity();
    float temp = dht.readTemperature();

    if (!isnan(hum) && !isnan(temp)) {
      // Calculate discomfort index
      float discomfort = ((9 * temp) / 5) - ((0.55 * (1 - (hum / 100))) * (((9 * temp) / 5) - 26)) + 32;

      // Update LCD display (the alarm message keeps the screen while active)
      if (!alarmActive) {
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("T: " + String((int)temp) + "C  H: " + String((int)hum) + "%");
        lcd.setCursor(0, 1);
        lcd.print("Discomfort: " + String((int)discomfort));
      }

      // Automated fan logic (if set to Auto Mode)
      if (fanAutoMode) {
        if (temp >= 28.0) {
          analogWrite(FAN_PIN, 255); // Full speed
        } else if (temp >= 25.0) {
          analogWrite(FAN_PIN, 120); // Half speed
        } else {
          analogWrite(FAN_PIN, 0);   // Off
        }
      }

      // Publish to MQTT (signed)
      publishSigned(TOPIC_TEMP, String(temp));
      publishSigned(TOPIC_HUMID, String(hum));
    } else {
      Serial.println("Failed to read from DHT sensor!");
    }
  }
}
