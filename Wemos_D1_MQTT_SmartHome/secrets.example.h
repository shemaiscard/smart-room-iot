// Copy this file to secrets.h (same folder) and fill in your own values.
// secrets.h is listed in .gitignore, so it never reaches GitHub.

#define WIFI_SSID      "YOUR_WIFI_SSID"
#define WIFI_PASSWORD  "YOUR_WIFI_PASSWORD"

// Broker. The defaults use the public HiveMQ broker over TLS. For a private
// broker (HiveMQ Cloud, Mosquitto) set its host, port and login here.
#define MQTT_HOST      "broker.hivemq.com"
#define MQTT_PORT      8883
#define MQTT_USE_TLS   1
#define MQTT_USER      ""   // empty: no login
#define MQTT_PASS      ""

// Topic prefix; must match TOPIC_BASE in the dashboard (default below)
// #define TOPIC_BASE  "giscard/smart_room"

// Shared secret: it encrypts and authenticates every message. Use the same value as SMART_ROOM_KEY in the dashboard's
// .streamlit/secrets.toml. Generate one with:
//   python -c "import secrets; print(secrets.token_hex(32))"
#define SMART_ROOM_KEY "CHANGE_ME_TO_A_LONG_RANDOM_STRING"
