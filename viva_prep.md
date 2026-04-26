# Individual Viva Preparation Guide (70 Marks)

Prepare for these common IoT and project-specific questions.

## 1. Project Specific Questions
- **Q: Why did you choose MQTT over HTTP?**
  - **A:** MQTT is a lightweight, publish-subscribe protocol designed for low-bandwidth, high-latency networks. It has a much smaller header size (2 bytes) compared to HTTP, making it ideal for battery-powered IoT devices and real-time data.
- **Q: How does the ESP32 connect to the dashboard?**
  - **A:** The ESP32 connects via WiFi to an MQTT Broker (like HiveMQ). It publishes sensor data to a specific topic (e.g., `room/temp`). The Streamlit dashboard is also an MQTT client that subscribes to that topic to receive and display data.
- **Q: What happens if the internet goes down?**
  - **A:** In the current prototype, cloud control would be lost. However, we can implement "Local Control" where the ESP32 handles basic automation (e.g., turning on lights if LDR value is low) even without internet connectivity.

## 2. Core IoT Concepts
- **Q: What are the four layers of IoT architecture?**
  - **A:** 
    1. **Sensing Layer** (Sensors/Actuators)
    2. **Network Layer** (Gateway, WiFi, MQTT)
    3. **Data Processing Layer** (Cloud, Analytics)
    4. **Application Layer** (User Interface/Dashboard)
- **Q: What is a "Broker" in MQTT?**
  - **A:** The broker is the central hub that receives all messages from publishers and routes them to subscribers based on the topic. It doesn't store data unless configured otherwise (retained messages).
- **Q: Explain the difference between DHT11 and DHT22.**
  - **A:** DHT22 has higher precision and a wider range for both temperature (-40 to 80°C) and humidity (0-100%) compared to DHT11.

## 3. Technical Implementation
- **Q: How do you handle "Quality of Service" (QoS) in MQTT?**
  - **A:** MQTT has 3 levels:
    - **QoS 0:** At most once (no guarantee).
    - **QoS 1:** At least once (acknowledged).
    - **QoS 2:** Exactly once (four-way handshake). We typically use QoS 0 or 1 for sensor data.
- **Q: What is "LDR" and how do you read its value?**
  - **A:** LDR is a Light Dependent Resistor. We use an Analog-to-Digital Converter (ADC) pin on the ESP32 to read a voltage value between 0 and 4095, which represents light intensity.

## 4. Problem Solving
- **Q: How would you scale this to a whole building?**
  - **A:** We would use multiple ESP32 nodes, potentially using a **Mesh Network** (like ESP-Mesh) or a **Gateway** architecture (LoRaWAN) if distance is an issue, and a more robust cloud backend like AWS IoT Core or Azure IoT Hub.
