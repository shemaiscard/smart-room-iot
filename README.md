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

1. **Firmware (Wemos_D1_MQTT_SmartHome.ino):** Runs on the Wemos D1. Reads sensors, drives actuators, connects to Wi-Fi, and communicates with the MQTT broker. Written in Arduino C++ using the ESP8266 core.
2. **MQTT Broker (broker.hivemq.com:1883):** Public broker used as the communication hub between the hardware and the dashboard. No authentication required.
3. **Dashboard (app.py):** Streamlit web application that subscribes to sensor topics, displays live telemetry charts, and publishes control commands to actuators.
4. **Simulator (simulator.py):** Optional script that generates synthetic sensor data for testing the dashboard without physical hardware.

### MQTT Topics

| Topic | Direction | Payload |
|-------|-----------|---------|
| giscard/smart_room/temp | Hardware to Dashboard | Temperature value in Celsius (float) |
| giscard/smart_room/hum | Hardware to Dashboard | Humidity value in percent (float) |
| giscard/smart_room/alarm | Hardware to Dashboard | "INTRUSION DETECTED!" (string) |
| giscard/smart_room/control | Dashboard to Hardware | Command in format DEVICE:STATE (e.g., LIGHT:RED, DOOR:UNLOCK, CAPS:ARM) |

### Supported Control Commands

| Device | Valid States |
|--------|-------------|
| LIGHT | WHITE, RED, GREEN, BLUE, YELLOW, OFF |
| DOOR | LOCK, UNLOCK |
| CAPS (Alarm) | ARM, DISARM |

---

## Dashboard Features

- **Live Telemetry Metrics:** Temperature, humidity, door lock status, and alarm mode displayed as metric cards.
- **Lighting Control:** 2x3 grid of color preset buttons (White, Red, Green, Blue, Yellow, OFF).
- **Door Lock Control:** Unlock and Lock buttons side by side.
- **Intruder Alarm Control:** Arm and Disarm buttons side by side. Intrusion alert banner appears when the IR sensor triggers.
- **Environment Trends Chart:** Plotly line chart showing temperature and humidity history over time.
- **Mobile Responsive:** CSS optimized for phone screens with forced horizontal button layouts.

---

## Setup

### Dashboard (Python)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the dashboard locally:

```bash
streamlit run app.py
```

### Firmware (Arduino IDE)

1. Open `Wemos_D1_MQTT_SmartHome.ino` in Arduino IDE.
2. Install the following libraries via Library Manager:
   - ESP8266WiFi (included with ESP8266 board package)
   - PubSubClient (by Nick O'Leary)
   - LiquidCrystal I2C (by Frank de Brabander)
   - Adafruit NeoPixel
   - DHT sensor library (by Adafruit)
   - Servo (included with ESP8266 board package)
3. Select board: **LOLIN(WEMOS) D1 R2 and mini**.
4. Set Wi-Fi credentials in the firmware (ssid and password variables).
5. Upload to the board.

### Testing Without Hardware

Run the simulator to generate synthetic sensor data:

```bash
python simulator.py
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

---

## Troubleshooting

- **No data on dashboard:** Verify the Wemos D1 is connected to the same Wi-Fi network and the MQTT broker is reachable. Check the Serial Monitor at 115200 baud for connection status.
- **LCD shows nothing:** Confirm the I2C address (0x27 or 0x3F). Run an I2C scanner sketch to detect the correct address.
- **Door servo not responding:** Verify the servo data wire is connected to pin D13. The servo and RGB LED pins are adjacent on the sensor shield and are commonly swapped by mistake.
- **Buttons stacked on mobile:** The dashboard uses CSS media queries to force horizontal button layouts. Clear the browser cache if the layout appears broken after an update.

---

## Project Structure

```
smart-room-iot-master/
  app.py                          -- Streamlit dashboard (live MQTT mode)
  Wemos_D1_MQTT_SmartHome.ino     -- Arduino firmware for Wemos D1
  simulator.py                    -- Synthetic sensor data generator
  requirements.txt                -- Python dependencies
  README.md                       -- This file
```

---

Developed as part of the Smart Room IoT project.
