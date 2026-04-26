import streamlit as st
import paho.mqtt.client as mqtt
import pandas as pd
import plotly.graph_objects as go
import time
import random
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Smart Room IoT Dashboard",
    page_icon="🏠",
    layout="wide",
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #161b22;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
    }
    </style>
    """, unsafe_allow_name=True)

# Session State Initialization
if 'temp_history' not in st.session_state:
    st.session_state.temp_history = []
if 'hum_history' not in st.session_state:
    st.session_state.hum_history = []
if 'time_history' not in st.session_state:
    st.session_state.time_history = []
if 'light_status' not in st.session_state:
    st.session_state.light_status = "OFF"
if 'fan_status' not in st.session_state:
    st.session_state.fan_status = "OFF"
if 'door_locked' not in st.session_state:
    st.session_state.door_locked = True

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
TOPIC_TEMP = "smart_room/sensors/temp"
TOPIC_HUM = "smart_room/sensors/hum"
TOPIC_CONTROL = "smart_room/control"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe([(TOPIC_TEMP, 0), (TOPIC_HUM, 0)])

def on_message(client, userdata, msg):
    try:
        val = float(msg.payload.decode())
        now = datetime.now().strftime("%H:%M:%S")
        if msg.topic == TOPIC_TEMP:
            st.session_state.temp_history.append(val)
        elif msg.topic == TOPIC_HUM:
            st.session_state.hum_history.append(val)
        st.session_state.time_history.append(now)
        
        # Keep only last 20 readings
        if len(st.session_state.temp_history) > 20:
            st.session_state.temp_history.pop(0)
            st.session_state.hum_history.pop(0)
            st.session_state.time_history.pop(0)
    except Exception as e:
        pass

# Sidebar
st.sidebar.title("⚙️ System Settings")
mode = st.sidebar.radio("Operation Mode", ["Simulated", "Live MQTT"])
st.sidebar.divider()
st.sidebar.info("This dashboard monitors environmental data and controls smart actuators via MQTT.")

# Mock Data Generation (Simulated Mode)
def generate_mock_data():
    t = 22 + random.uniform(-1, 1)
    h = 45 + random.uniform(-2, 2)
    now = datetime.now().strftime("%H:%M:%S")
    
    st.session_state.temp_history.append(t)
    st.session_state.hum_history.append(h)
    st.session_state.time_history.append(now)
    
    if len(st.session_state.temp_history) > 20:
        st.session_state.temp_history.pop(0)
        st.session_state.hum_history.pop(0)
        st.session_state.time_history.pop(0)

# MQTT Setup
if 'mqtt_client' not in st.session_state and mode == "Live MQTT":
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        st.session_state.mqtt_client = client
        st.sidebar.success("✅ Connected to MQTT Broker")
    except Exception as e:
        st.sidebar.error(f"❌ MQTT Connection Failed: {e}")

# Main Dashboard
st.title("🏠 Smart Room Control Center")
st.markdown("---")

# Layout: 3 Columns for metrics
col1, col2, col3 = st.columns(3)

if mode == "Simulated":
    generate_mock_data()
    current_temp = st.session_state.temp_history[-1] if st.session_state.temp_history else 0
    current_hum = st.session_state.hum_history[-1] if st.session_state.hum_history else 0
else:
    # Use real data from MQTT
    current_temp = st.session_state.temp_history[-1] if st.session_state.temp_history else 0
    current_hum = st.session_state.hum_history[-1] if st.session_state.hum_history else 0

with col1:
    st.metric("🌡️ Temperature", f"{current_temp:.1f} °C", delta=f"{random.uniform(-0.5, 0.5):.1f}" if mode == "Simulated" else None)

with col2:
    st.metric("💧 Humidity", f"{current_hum:.1f} %", delta=f"{random.uniform(-1, 1):.1f}" if mode == "Simulated" else None)

with col3:
    status_color = "🟢 Secure" if st.session_state.door_locked else "🔴 Unlocked"
    st.metric("🔐 Security Status", status_color)

st.markdown("### 📊 Real-Time Environmental Trends")
# Chart
fig = go.Figure()
if st.session_state.time_history:
    fig.add_trace(go.Scatter(x=st.session_state.time_history, y=st.session_state.temp_history, name="Temp (°C)", line=dict(color='#FF4B4B', width=2)))
    fig.add_trace(go.Scatter(x=st.session_state.time_history, y=st.session_state.hum_history, name="Hum (%)", line=dict(color='#0068C9', width=2)))
fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("### 🎮 Remote Control Panel")
ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)

with ctrl_col1:
    st.write("💡 **Main Lights**")
    if st.button(f"Turn {('OFF' if st.session_state.light_status == 'ON' else 'ON')}"):
        st.session_state.light_status = "OFF" if st.session_state.light_status == "ON" else "ON"
        if mode == "Live MQTT" and 'mqtt_client' in st.session_state:
            st.session_state.mqtt_client.publish(TOPIC_CONTROL, f"LIGHT:{st.session_state.light_status}")
    st.info(f"Status: {st.session_state.light_status}")

with ctrl_col2:
    st.write("🌀 **Ceiling Fan**")
    if st.button(f"Toggle Fan {('Stop' if st.session_state.fan_status == 'ON' else 'Start')}"):
        st.session_state.fan_status = "OFF" if st.session_state.fan_status == "ON" else "ON"
        if mode == "Live MQTT" and 'mqtt_client' in st.session_state:
            st.session_state.mqtt_client.publish(TOPIC_CONTROL, f"FAN:{st.session_state.fan_status}")
    st.info(f"Status: {st.session_state.fan_status}")

with ctrl_col3:
    st.write("🔓 **Door Lock**")
    if st.button(f"{('Unlock' if st.session_state.door_locked else 'Lock')} Door"):
        st.session_state.door_locked = not st.session_state.door_locked
        if mode == "Live MQTT" and 'mqtt_client' in st.session_state:
            action = "LOCK" if st.session_state.door_locked else "UNLOCK"
            st.session_state.mqtt_client.publish(TOPIC_CONTROL, f"DOOR:{action}")
    st.info(f"Status: {('LOCKED' if st.session_state.door_locked else 'UNLOCKED')}")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | MQTT Broker: {MQTT_BROKER}")

# Auto-refresh logic
time.sleep(2)
st.rerun()
