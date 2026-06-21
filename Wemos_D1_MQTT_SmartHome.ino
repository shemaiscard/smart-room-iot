#include <I2S.h>

// Wemos D1 MQTT Smart Home Kit Integration Code
// Tailored for Wemos D1 R1/R2 and ESP8266 based boards

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Adafruit_NeoPixel.h>
#include <Servo.h>
#include "DHT.h"

// ==================== CONFIGURATION ====================
// Replace with your local Wi-Fi details (or mobile hotspot)
const char* ssid = "YOUR_WIFI_SSID";         // Replace with your Wi-Fi network name before uploading
const char* password = "YOUR_WIFI_PASSWORD";   // Replace with your Wi-Fi password before uploading

// MQTT Broker (using free public broker broker.hivemq.com for easy testing)
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;

// Unique client identifier prefix
const char* client_id_prefix = "WemosSmartHome-";
// ========================================================

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
#define DHTTYPE      DHT11
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

WiFiClient espClient;
PubSubClient client(espClient);

// States and variables
bool capsMode = false;      // Security / Intruder Alarm mode
bool fanAutoMode = true;    // True: Fan turns on automatically based on temp. False: manual MQTT control.
int tones[] = { 261, 523 };  // Warning alarm tones
unsigned long lastPublishTime = 0;
const unsigned long publishInterval = 10000; // Publish telemetry every 10 seconds

// MQTT Topics (aligned with Streamlit app)
const char* TOPIC_CONTROL    = "giscard/smart_room/control"; // Subscribed control topic (device:state)
const char* TOPIC_STATUS     = "giscard/smart_room/status";  // Debug/connection status
const char* TOPIC_TEMP       = "giscard/smart_room/temp";    // Telemetry output: temperature
const char* TOPIC_HUMID      = "giscard/smart_room/hum";     // Telemetry output: humidity
const char* TOPIC_ALARM      = "giscard/smart_room/alarm";   // Alarm events output

void setup_wifi() {
  delay(10);
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(ssid);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Connecting Wi-Fi");

  WiFi.begin(ssid, password);
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

// Function to set RGB Neopixels
void setLEDColor(uint8_t r, uint8_t g, uint8_t b) {
  for (int i = 0; i < 3; i++) {
    RGB_LED.setPixelColor(i, r, g, b);
  }
  RGB_LED.show();
}

// Play alarm sound and flash lights
void triggerIntruderAlert() {
  Serial.println("INTRUSION DETECTED! Triggering Alarm.");
  client.publish(TOPIC_ALARM, "INTRUSION DETECTED!");
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("!!! EMERGENCY !!!");
  lcd.setCursor(0, 1);
  lcd.print("INTRUDER DETECTED");

  for (int repeat = 0; repeat < 5; repeat++) {
    // Red flash + High pitch
    setLEDColor(255, 0, 0);
    tone(PIEZO_PIN, tones[1]);
    delay(300);
    
    // Blue flash + Low pitch
    setLEDColor(0, 0, 255);
    tone(PIEZO_PIN, tones[0]);
    delay(300);
  }
  noTone(PIEZO_PIN);
  setLEDColor(0, 0, 0);
  lcd.clear();
}

// Handles incoming MQTT messages
void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  message.trim();
  
  Serial.print("MQTT Received [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(message);

  if (String(topic) == TOPIC_CONTROL) {
    int colonIndex = message.indexOf(':');
    if (colonIndex > 0) {
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
          noTone(PIEZO_PIN);
        }
      }
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = client_id_prefix + String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println("Connected to MQTT Broker!");
      client.publish(TOPIC_STATUS, "SmartHome Online");
      
      // Subscribe to control topic
      client.subscribe(TOPIC_CONTROL);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" Retrying in 5 seconds...");
      delay(5000);
    }
  }
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
  
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  // MQTT loop
  if (WiFi.status() == WL_CONNECTED) {
    if (!client.connected()) {
      reconnect();
    }
    client.loop();
  }

  // Security mode: check IR sensor
  if (capsMode && digitalRead(IR_PIN) == LOW) {
    triggerIntruderAlert();
  }

  // Telemetry publish and LCD display updates
  unsigned long currentMillis = millis();
  if (currentMillis - lastPublishTime >= publishInterval) {
    lastPublishTime = currentMillis;

    float hum = dht.readHumidity();
    float temp = dht.readTemperature();

    if (!isnan(hum) && !isnan(temp)) {
      // Calculate discomfort index
      float discomfort = ((9 * temp) / 5) - ((0.55 * (1 - (hum / 100))) * (((9 * temp) / 5) - 26)) + 32;

      // Update LCD display
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("T: " + String((int)temp) + "C  H: " + String((int)hum) + "%");
      lcd.setCursor(0, 1);
      lcd.print("Discomfort: " + String((int)discomfort));

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

      // Publish to MQTT
      if (WiFi.status() == WL_CONNECTED && client.connected()) {
        client.publish(TOPIC_TEMP, String(temp).c_str());
        client.publish(TOPIC_HUMID, String(hum).c_str());
      }
    } else {
      Serial.println("Failed to read from DHT sensor!");
    }
  }
}
