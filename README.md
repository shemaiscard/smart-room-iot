# Smart Room IoT Dashboard 

A premium, live IoT monitoring and control system built with **Streamlit** and **MQTT**. This project allows you to monitor room environment data (Temperature & Humidity) and control actuators (Lights, Fan, Door) in real-time.

live demo : https://smart-room-iot.streamlit.app/

## How it Works (The Workflow)

The system consists of three main parts that work together:

1.  **The Simulator (`simulator.py`)**: 
    - This script acts as your "ESP32 Device." 
    - It generates random sensor data and sends it to a public server (the MQTT Broker) every 5 seconds.
    - It uses a unique topic prefix (`giscard/smart_room/...`) to ensure your data doesn't get mixed up with others.

2.  **The MQTT Broker (`broker.hivemq.com`)**: 
    - This is the "Post Office." 
    - It receives messages from the simulator and holds them until the dashboard asks for them.

3.  **The Dashboard (`app.py`)**: 
    - This is the "User Interface" hosted on Streamlit Cloud.
    - It connects to the same Post Office (Broker) and listens for sensor updates.
    - **Pro Tip:** We use a `queue.Queue` (Thread-Safe Bridge) to ensure the background data updates don't crash the UI.

---

##  Step-by-Step Setup

### 1. Requirements
Ensure you have the dependencies installed. If running locally:
```bash
pip install -r requirements.txt
```

### 2. Start the Simulation
On your local PC, run the simulator script. This represents your hardware sending data:
```bash
python simulator.py
```
*Wait for it to say "Connected successfully!" and start publishing.*

### 3. Open the Dashboard
Visit your Streamlit URL (e.g., `https://smart-room-iot.streamlit.app`).
- Set the **Operation Mode** in the sidebar to **"Live MQTT"**.
- You will see a green status bar: **"● Receiving Live Data"**.
- The graph and metrics will update automatically every time the simulator sends a pulse.

---

##  File Explanations for the Team

### `app.py`
This is the main application. 
- **MQTT Callbacks:** `on_connect` and `on_message` handle the background connection.
- **The Queue Bridge:** Because MQTT runs in a background thread, it puts data into a `data_queue`. The main loop then picks it up to update `st.session_state`.
- **Plotly Integration:** Used for the smooth, dark-themed historical graph.

### `simulator.py`
A lightweight script using the `paho-mqtt` library.
- It publishes to two topics: `temp` and `hum`.
- It uses **Unique Client IDs** to prevent being kicked off the server if multiple people run it.

### `requirements.txt`
Critical file for Streamlit Cloud.
- We have pinned `paho-mqtt==1.6.1` to ensure maximum compatibility between the Cloud and local computers.

---

## 🔧 Troubleshooting Fixes (Already Implemented)
- **Problem:** Data wasn't showing up on Live MQTT.
- **Cause:** Streamlit's UI thread and the MQTT background thread were conflicting.
- **Fix:** We implemented a `queue.Queue` to safely pass data between threads. Now, even if the library versions differ slightly, the data is captured reliably.

---

**Developed for the Smart Room IoT Project.**
