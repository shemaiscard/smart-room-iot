# Smart Room IoT Control System

A real-time IoT monitoring and control system that connects a Wemos D1 microcontroller to a Streamlit web dashboard over MQTT. The system reads environmental sensor data, controls actuators (RGB lighting, electronic door lock, intruder alarm), and displays live telemetry on a mobile-friendly dashboard.

## Live Dashboard

Hosted on Streamlit Cloud: [smart-room-iot.streamlit.app](https://smart-room-iot.streamlit.app/)

---

## Hardware

### Microcontroller

- **Board:** LOLIN (Wemos) D1 R2 and mini (ESP8266-based)
- **Board Profile in Arduino IDE:** LOLIN(WEMOS) D1 R2 and mini
- **Clock Frequency:** 80 MHz
- **Flash Size:** 4MB
- **Upload Speed:** 115200 baud

### Sensors

| Sensor | Model | Pin | Purpose |
|--------|-------|-----|---------|
| Temperature and Humidity | DHT11 | D8 | Reads ambient temperature (Celsius) and relative humidity (%). Published to the dashboard every 10 seconds for environmental monitoring. |
| Infrared Motion Sensor | IR Obstacle Sensor | D9 | Detects physical intrusion when the alarm is armed. Triggers an audible and visual alert sequence when motion is detected. |

### Actuators

| Actuator | Model | Pin | Purpose |
|----------|-------|-----|---------|
| RGB LED Strip | WS2812B NeoPixel (3 LEDs) | D6 | Provides room lighting with preset color options (White, Red, Green, Blue, Yellow, OFF). Controlled remotely via the dashboard. |
| Servo Motor | SG90 Micro Servo | D13 | Acts as an electronic door lock. Rotates to 90 degrees (unlocked) or 180 degrees (locked) based on dashboard commands. |
| Piezo Buzzer | Passive Piezo | D7 | Produces an alarm siren (alternating tones at 261 Hz and 523 Hz) when the IR sensor detects motion while the alarm is armed. |
| Cooling Fan | DC Mini Fan | D11 | Operates in automatic mode by default. Turns on at full speed above 28C, half speed above 25C, and off below 25C. Not exposed on the dashboard. |
| LCD Display | 16x2 I2C LCD (address 0x27) | SDA/SCL (D14/D15) | Displays Wi-Fi connection status, IP address, live temperature/humidity readings, and discomfort index locally on the device. |

### Why These Sensors Were Chosen

- **DHT11:** Inexpensive, widely available, and sufficient for indoor temperature and humidity monitoring at the accuracy level needed for a smart room prototype. It provides both readings from a single pin.
- **IR Obstacle Sensor:** Simple digital output (HIGH/LOW) makes it straightforward to integrate as a motion trigger for the security system without complex signal processing.

---

## Software Architecture

### System Components

1. **Firmware (Wemos_D1_MQTT_SmartHome/):** Runs on the Wemos D1. Reads sensors, drives actuators, connects to Wi-Fi, and communicates with the MQTT broker. Written in Arduino C++ using the ESP8266 core.
2. **MQTT Broker (broker.hivemq.com:8883, TLS):** Public broker used as the communication hub between the hardware and the dashboard. Any other broker (HiveMQ Cloud, Mosquitto) can be set in the secrets.
3. **Dashboard (app.py):** Streamlit web application that subscribes to sensor topics, displays live telemetry charts, and publishes control commands to actuators.
4. **Message sealing (secure_msg.py):** Encrypts and authenticates every MQTT message; the firmware has the same code in C (`SecureMsg.h`).
5. **Simulator (simulator.py):** Optional script that stands in for the board and publishes sealed synthetic readings.

### Security

The broker is public, so anyone can connect to it. The system protects itself as follows:

- **TLS:** the board and the dashboard connect on port 8883 and check the broker's certificate (the board trusts Amazon Root CA 1, which signs broker.hivemq.com).
- **Sealed messages:** every reading, alarm, command and status is encrypted and authenticated with AES-256-GCM under a key derived from a secret shared by the board and the dashboard (`<timestamp ms>|<hex of nonce + ciphertext + tag>`, with the topic and timestamp authenticated too). Anyone on the broker sees only ciphertext. Messages that fail authentication, carry a timestamp more than 30 s off, or (for commands) a timestamp not newer than the last accepted one are dropped, so a stranger cannot read the room, unlock the door, fake an alarm or replay a recorded command.
- **Dashboard password:** in live mode the controls stay disabled until the dashboard password is entered. After 5 wrong passwords in 10 minutes, unlocking is blocked for 10 minutes.
- **Simulation stays local:** simulation mode never publishes to the broker.
- **Online status:** at each connection the board starts a session and registers a sealed last-will message for it, so the dashboard shows when it goes offline. An old last will replayed later names an older session and is ignored, and any new authentic reading marks the board online again.

On the public broker, anyone can still see *that* messages flow and could flood the topics. A private broker with a login per device removes that too; see below.

### MQTT Topics

Every payload is sealed: `<timestamp ms>|<hex of nonce (12 bytes) + ciphertext + tag (16 bytes)>`. The table lists the body inside.

| Topic | Direction | Body |
|-------|-----------|---------|
| giscard/smart_room/temp | Hardware to Dashboard | Temperature value in Celsius (float) |
| giscard/smart_room/hum | Hardware to Dashboard | Humidity value in percent (float) |
| giscard/smart_room/alarm | Hardware to Dashboard | "INTRUSION DETECTED!" (string) |
| giscard/smart_room/status | Hardware to Dashboard | "online:&lt;session&gt;" (retained) or "offline:&lt;session&gt;" (last will) |
| giscard/smart_room/control | Dashboard to Hardware | Command in format DEVICE:STATE (e.g., LIGHT:RED, DOOR:UNLOCK, CAPS:ARM), QoS 1 |

### Supported Control Commands

| Device | Valid States |
|--------|-------------|
| LIGHT | WHITE, RED, GREEN, BLUE, YELLOW, OFF |
| DOOR | LOCK, UNLOCK |
| CAPS (Alarm) | ARM, DISARM |

---

## Dashboard Features

- **Built-in Hardware Simulation Mode:** Active by default so the hosted dashboard can be fully tested without physical hardware connected. Includes realistic sensor drift, adjustable target temperatures/humidity, and manual intrusion trigger testing. Nothing is sent to the broker in this mode.
- **Live Mode:** Shows only authentic (sealed) readings from the board, counts rejected messages, and unlocks the controls with the dashboard password.
- **Live Telemetry Metrics:** Temperature, humidity, door lock status, and alarm mode displayed as metric cards with dynamic deltas.
- **Lighting Control:** 2x3 grid of color preset buttons (White, Red, Green, Blue, Yellow, OFF) with live LED indicator previews.
- **Door Lock Control:** Unlock and Lock buttons side by side with real-time lock status and servo angle state.
- **Intruder Alarm Control:** Arm and Disarm buttons side by side. Intrusion alert banner appears when the IR sensor or simulation triggers.
- **Environment Trends Chart:** Plotly line chart showing temperature and humidity history over time.
- **Mobile Responsive:** CSS optimized for phone screens with forced horizontal button layouts.

---

## Setup

### Dashboard (Python)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. For live mode, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set `SMART_ROOM_KEY` and `DASHBOARD_PASSWORD` (on Streamlit Cloud, paste the same lines into the app's Secrets panel). Simulation mode needs no secrets.

3. Run the dashboard locally:

```bash
streamlit run app.py
```

### Firmware (Arduino IDE)

1. Open `Wemos_D1_MQTT_SmartHome/Wemos_D1_MQTT_SmartHome.ino` in Arduino IDE.
2. Install the following libraries via Library Manager:
   - ESP8266WiFi (included with ESP8266 board package)
   - PubSubClient (by Nick O'Leary)
   - LiquidCrystal I2C (by Frank de Brabander)
   - Adafruit NeoPixel
   - DHT sensor library (by Adafruit)
   - Servo (included with ESP8266 board package)
3. Select board: **LOLIN(WEMOS) D1 R2 and mini**.
4. Copy `secrets.example.h` to `secrets.h` in the same folder and fill in the Wi-Fi details and the same `SMART_ROOM_KEY` as the dashboard. `secrets.h` is ignored by Git.
5. Upload to the board. It sets its clock over NTP before connecting (needed for TLS and for message timestamps).
6. For finer readings, replace the DHT11 with a DHT22 and change `DHTTYPE` to `DHT22`.
7. **Pin conflict:** on the Wemos D1, the D7 (buzzer) and D11 (fan) headers are the same chip pin, GPIO 13, so the buzzer and the fan switch together. The firmware prints a compiler warning about it. Wire one of them to a free pin and change `PIEZO_PIN` or `FAN_PIN`.

### Private Broker (recommended)

A free HiveMQ Cloud cluster gives the system its own broker with a login per client:

1. Create a free Serverless cluster at console.hivemq.cloud and note its host name (port 8883, TLS).
2. Under Access Management, create two credentials: one for the board and one for the dashboard. Where permissions can be set, let only the dashboard publish to the `control` topic and only the board publish to the others.
3. In `secrets.h`, set `MQTT_HOST`, `MQTT_USER` and `MQTT_PASS` to the board's login. HiveMQ Cloud certificates have been issued by Let's Encrypt, so replace `BROKER_CA` in the sketch with that root (ISRG Root X1 at the time of writing; `openssl s_client -connect HOST:8883 -showcerts` shows the chain).
4. In the dashboard secrets, set `MQTT_HOST`, `MQTT_USER` and `MQTT_PASS` to the dashboard's login.

### Testing Without Hardware

Run the simulator to publish sealed synthetic readings (same key as the dashboard):

```bash
SMART_ROOM_KEY=your-key python simulator.py
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| streamlit | Web dashboard framework |
| paho-mqtt 1.6.1 | MQTT client for Python |
| pandas | Data handling |
| plotly | Interactive charting |
| numpy | Numerical operations |
| pycryptodome | AES-256-GCM for sealed messages |

---

## Troubleshooting

- **No data on dashboard:** Verify the Wemos D1 is connected to Wi-Fi and the MQTT broker is reachable. Check the Serial Monitor at 115200 baud for connection status; a `tls=` message there means the certificate check failed (usually the clock is not set yet).
- **"Rejected forged, stale or unreadable messages" keeps growing:** the board and the dashboard use different keys, or the board's clock is wrong.
- **LCD shows nothing:** Confirm the I2C address (0x27 or 0x3F). Run an I2C scanner sketch to detect the correct address.
- **Door servo not responding:** Verify the servo data wire is connected to pin D13. The servo and RGB LED pins are adjacent on the sensor shield and are commonly swapped by mistake.
- **Buttons stacked on mobile:** The dashboard uses CSS media queries to force horizontal button layouts. Clear the browser cache if the layout appears broken after an update.

---

## Project Structure

```
smart-room-iot-master/
  app.py                          -- Streamlit dashboard (live MQTT mode)
  secure_msg.py                   -- Message sealing shared by dashboard and simulator
  Wemos_D1_MQTT_SmartHome/        -- Arduino firmware for Wemos D1 (+ SecureMsg.h, secrets.example.h)
  simulator.py                    -- Sealed synthetic sensor data generator
  .streamlit/secrets.toml.example -- Dashboard secrets template
  requirements.txt                -- Python dependencies
  README.md                       -- This file
```

---

Developed as part of the Smart Room IoT project.
