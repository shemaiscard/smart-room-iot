# Project PPT Content: Smart Room Monitoring & Control System

**Project Title:** Smart Room: IoT-Based Environmental Monitoring and Automated Control System
**Course:** Internet of Things (IoT)
**Group Members:** [Names]

---

## Slide 1: Title Slide
- **Project Name:** Smart Room: IoT-Based Environmental Monitoring and Automated Control System
- **Objective:** Enhancing room comfort and safety through real-time data and remote automation.
- **Presenter:** [Your Name / Group Leader]

---

## Slide 2: Problem Definition
- **The Issue:** Traditional rooms lack real-time monitoring of environmental factors (temperature, humidity, light).
- **Inefficiency:** Energy is wasted on fans or lights left on when not needed.
- **Safety:** Risks like gas leaks or motion in unauthorized areas are often undetected.
- **Goal:** Narrowing the focus to a single "Smart Room" to create a manageable, scalable prototype for home automation.

---

## Slide 3: Technologies Used (Hardware)
- **Microcontroller:** ESP32 (Built-in WiFi and Bluetooth)
- **Sensors:**
  - DHT11/DHT22 (Temperature & Humidity)
  - LDR (Light Dependent Resistor) for light intensity
  - PIR Sensor (Passive Infrared) for motion detection
  - MQ-2/MQ-5 (Gas/Smoke Sensor - Optional)
- **Actuators:**
  - 5V Relay Module (to control AC Fan/Light)
  - SG90 Servo Motor (for Smart Door Lock simulation)
  - LEDs (Status Indicators)
- **Communication:** MQTT Protocol (Message Queuing Telemetry Transport)

---

## Slide 4: Technologies Used (Software)
- **Programming Language:** C++ (Arduino IDE) for hardware; Python for Dashboard.
- **Cloud/Broker:** HiveMQ or Mosquitto (MQTT Broker).
- **Dashboard:** Streamlit (Python-based Web App) or JavaScript Dashboard.
- **Data Visualization:** Plotly/Chart.js for real-time graphs.
- **Deployment:** Streamlit Cloud or Netlify.

---

## Slide 5: Evidence of Progress (Prototype & Code)
- **Hardware Status:** Prototype assembled on breadboard (Reference images in folder).
- **Communication:** Successfully established MQTT connection between ESP32 and Broker.
- **Dashboard:** Functional UI showing real-time sensor updates.
- **Data Flow:** `Sensor` -> `ESP32` -> `MQTT Broker` -> `Cloud Dashboard`.

---

## Slide 6: Challenges and Next Steps
- **Challenges:**
  - MQTT latency issues in unstable networks.
  - Power management for battery-operated sensors.
  - Ensuring secure communication (SSL/TLS).
- **Next Steps:**
  - Integrating voice control (Alexa/Google Assistant).
  - Implementing data persistence (SQL/NoSQL) for historical analysis.
  - Designing a custom PCB for a more robust form factor.

---

## Slide 7: Conclusion & Q&A
- Summary of the impact on energy efficiency and user convenience.
- Open for questions.
