# 🏠 Smart Room IoT Dashboard

An IoT-based **Smart Room Monitoring and Control System** built for the Internet of Things course midterm project.

## Features
- 🌡️ Real-time Temperature & Humidity monitoring
- 💡 Remote control of Lights, Fan, and Door Lock
- 📊 Live trend graphs via Plotly
- 📡 MQTT integration (HiveMQ Broker)
- 🖥️ Simulated mode for demo without hardware

## Tech Stack
- **Hardware:** ESP32, DHT11, PIR Sensor, Relay Module, LDR
- **Protocol:** MQTT (HiveMQ Cloud)
- **Dashboard:** Python + Streamlit + Plotly
- **Broker:** `broker.hivemq.com`

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

To simulate sensor data (no hardware needed):

```bash
python simulator.py
```

## Deployment
Deploy instantly on [Streamlit Cloud](https://streamlit.io/cloud):
1. Push this repo to GitHub
2. Go to streamlit.io/cloud → New App
3. Select this repo and `app.py`

## MQTT Topics
| Topic | Description |
|---|---|
| `smart_room/sensors/temp` | Temperature data |
| `smart_room/sensors/hum` | Humidity data |
| `smart_room/control` | Control commands |
