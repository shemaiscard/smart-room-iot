import streamlit as st
import paho.mqtt.client as mqtt
import pandas as pd
import plotly.graph_objects as go
import time
import random
from datetime import datetime
import queue

# Page Configuration
st.set_page_config(
    page_title="Smart Room Control Center",
    layout="wide",
)

# Custom CSS for Premium Dark Mode, Control Cards, and Mobile Grid Layout
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #0f172a);
        color: #f8fafc;
    }
    
    /* Metrics Card styling */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #38bdf8 !important;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.95rem !important;
        color: #94a3b8 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Styled Containers (replacing the empty card divs to avoid mobile spacing issues) */
    .st-key-lights_card, .st-key-door_card, .st-key-alarm_card {
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Title gradient */
    .gradient-title {
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 5px;
    }
    
    /* Status indicators */
    .status-badge {
        padding: 6px 14px;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 15px;
    }
    .status-online {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .status-waiting {
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .status-offline {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Style normal buttons */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
        color: white;
        border: none;
        padding: 10px 14px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #6366f1 0%, #60a5fa 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }

    /* Lights card compact layout */
    .st-key-lights_card {
        padding: 10px !important;
    }
    .st-key-lights_card h4 {
        margin-top: 0 !important;
        margin-bottom: 2px !important;
    }
    .st-key-lights_card p {
        margin-bottom: 4px !important;
    }
    .st-key-lights_card div[data-testid="stVerticalBlock"] {
        gap: 4px !important;
    }
    .st-key-lights_card .stButton>button {
        width: 100% !important;
    }

    /* Force lights grid 3-across, door/alarm buttons 2-across on ALL screens */
    @media (max-width: 640px) {
        .st-key-lights_card div[data-testid="stHorizontalBlock"],
        .st-key-door_card div[data-testid="stHorizontalBlock"],
        .st-key-alarm_card div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 4px !important;
        }
        .st-key-lights_card div[data-testid="stHorizontalBlock"] > div {
            width: 33.33% !important;
            flex: 0 0 33.33% !important;
            min-width: 0 !important;
        }
        .st-key-door_card div[data-testid="stHorizontalBlock"] > div,
        .st-key-alarm_card div[data-testid="stHorizontalBlock"] > div {
            width: 50% !important;
            flex: 0 0 50% !important;
            min-width: 0 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Global Data Bridge (Thread-safe)
if 'data_queue' not in st.session_state:
    st.session_state.data_queue = queue.Queue()

# Session State for History & Control
if 'temp_history' not in st.session_state:
    st.session_state.temp_history = []
if 'hum_history' not in st.session_state:
    st.session_state.hum_history = []
if 'time_history' not in st.session_state:
    st.session_state.time_history = []
if 'light_status' not in st.session_state:
    st.session_state.light_status = "OFF"
if 'door_locked' not in st.session_state:
    st.session_state.door_locked = True
if 'caps_mode' not in st.session_state:
    st.session_state.caps_mode = False
if 'last_mqtt_update' not in st.session_state:
    st.session_state.last_mqtt_update = None
if 'alarm_triggered' not in st.session_state:
    st.session_state.alarm_triggered = False

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
TOPIC_TEMP = "giscard/smart_room/temp"
TOPIC_HUM = "giscard/smart_room/hum"
TOPIC_ALARM = "giscard/smart_room/alarm"
TOPIC_CONTROL = "giscard/smart_room/control"

# Callback for MQTT Messages
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe([(TOPIC_TEMP, 0), (TOPIC_HUM, 0), (TOPIC_ALARM, 0)])

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload_str = msg.payload.decode()
        if topic == TOPIC_ALARM:
            userdata['queue'].put((topic, payload_str))
        else:
            val = float(payload_str)
            userdata['queue'].put((topic, val))
    except Exception as e:
        pass

# Sidebar: System configuration and connection logs
st.sidebar.markdown("### MQTT Network Info")
st.sidebar.markdown(f"**Broker:** `{MQTT_BROKER}`")
st.sidebar.markdown(f"**Port:** `{MQTT_PORT}`")
st.sidebar.markdown("---")
st.sidebar.markdown("**Subscribed Topics:**")
st.sidebar.markdown(f"- `{TOPIC_TEMP}`")
st.sidebar.markdown(f"- `{TOPIC_HUM}`")
st.sidebar.markdown(f"- `{TOPIC_ALARM}`")
st.sidebar.markdown("---")
st.sidebar.markdown("**Publish Topic:**")
st.sidebar.markdown(f"- `{TOPIC_CONTROL}`")

# Establish MQTT Connection
if 'mqtt_client' not in st.session_state:
    client_id = f"giscard-dash-{random.randint(1000, 9999)}"
    client = mqtt.Client(client_id=client_id, userdata={'queue': st.session_state.data_queue})
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        st.session_state.mqtt_client = client
        st.sidebar.success(f"Connected: {client_id}")
    except Exception as e:
        st.sidebar.error(f"Connection Failed: {e}")

# Process Queue Data in the Main Thread
while not st.session_state.data_queue.empty():
    topic, val = st.session_state.data_queue.get()
    now = datetime.now().strftime("%H:%M:%S")
    st.session_state.last_mqtt_update = datetime.now()
    
    if topic == TOPIC_ALARM:
        st.session_state.alarm_triggered = True
    else:
        last_temp = st.session_state.temp_history[-1] if st.session_state.temp_history else 0.0
        last_hum = st.session_state.hum_history[-1] if st.session_state.hum_history else 0.0

        if topic == TOPIC_TEMP:
            st.session_state.temp_history.append(val)
            st.session_state.hum_history.append(last_hum)
        elif topic == TOPIC_HUM:
            st.session_state.temp_history.append(last_temp)
            st.session_state.hum_history.append(val)
        
        st.session_state.time_history.append(now)
        
        # Keep history length bounded
        if len(st.session_state.temp_history) > 30:
            st.session_state.temp_history.pop(0)
            st.session_state.hum_history.pop(0)
            st.session_state.time_history.pop(0)

# Main Dashboard UI
st.markdown('<div class="gradient-title">Smart Room Control Center</div>', unsafe_allow_html=True)
st.markdown("<p style='color: #64748b; font-size: 1.1rem; margin-top: -10px;'>Live MQTT Telemetry & Hardware Actuator Control</p>", unsafe_allow_html=True)

# Connection Status Header
if st.session_state.last_mqtt_update:
    secs_ago = (datetime.now() - st.session_state.last_mqtt_update).total_seconds()
    if secs_ago < 15:
        st.markdown('<span class="status-badge status-online">● LIVE: Receiving Sensor Data</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="status-badge status-waiting">● STANDBY: No updates in {int(secs_ago)}s</span>', unsafe_allow_html=True)
else:
    st.markdown('<span class="status-badge status-offline">● OFFLINE: Waiting for hardware data...</span>', unsafe_allow_html=True)

# Critical Alarm Banner
if st.session_state.alarm_triggered:
    st.error("INTRUSION DETECTED! The hardware alarm was triggered by the IR Sensor. Please verify the room safety.")
    if st.button("Clear / Disarm Alarm"):
        st.session_state.alarm_triggered = False
        if 'mqtt_client' in st.session_state:
            st.session_state.mqtt_client.publish(TOPIC_CONTROL, "SECURITY:OFF")
        st.rerun()

st.markdown("---")

# Metrics Section (Temperature, Humidity, Door Status, Security Mode)
col1, col2, col3, col4 = st.columns(4)

curr_t = st.session_state.temp_history[-1] if st.session_state.temp_history else 0.0
curr_h = st.session_state.hum_history[-1] if st.session_state.hum_history else 0.0

with col1:
    st.metric("Temperature", f"{curr_t:.1f} °C" if curr_t > 0 else "Waiting...")
with col2:
    st.metric("Humidity", f"{curr_h:.1f} %" if curr_h > 0 else "Waiting...")
with col3:
    st.metric("Door Lock", "LOCKED" if st.session_state.door_locked else "UNLOCKED")
with col4:
    st.metric("Alarm Mode", "ARMED" if st.session_state.caps_mode else "DISARMED")

st.markdown("---")

# Remote Control Section
st.markdown("### Hardware Control Panel")

def send_cmd(device, state):
    if 'mqtt_client' in st.session_state:
        st.session_state.mqtt_client.publish(TOPIC_CONTROL, f"{device}:{state}")

c1, c2, c3 = st.columns(3, gap="small")

# 1. Lights (Grid of 2 Rows and 3 Columns)
with c1:
    with st.container(key="lights_card"):
        st.markdown("#### Lighting System")
        st.write(f"Current State: **{st.session_state.light_status}**")
        
        # Row 1
        r1c1, r1c2, r1c3 = st.columns(3, gap="small")
        with r1c1:
            if st.button("White", key="light_white"):
                st.session_state.light_status = "WHITE"
                send_cmd("LIGHT", "WHITE")
        with r1c2:
            if st.button("Red", key="light_red"):
                st.session_state.light_status = "RED"
                send_cmd("LIGHT", "RED")
        with r1c3:
            if st.button("Green", key="light_green"):
                st.session_state.light_status = "GREEN"
                send_cmd("LIGHT", "GREEN")
                
        # Row 2
        r2c1, r2c2, r2c3 = st.columns(3, gap="small")
        with r2c1:
            if st.button("Blue", key="light_blue"):
                st.session_state.light_status = "BLUE"
                send_cmd("LIGHT", "BLUE")
        with r2c2:
            if st.button("Yellow", key="light_yellow"):
                st.session_state.light_status = "YELLOW"
                send_cmd("LIGHT", "YELLOW")
        with r2c3:
            if st.button("OFF", key="light_off"):
                st.session_state.light_status = "OFF"
                send_cmd("LIGHT", "OFF")

# 2. Door Lock Control
with c2:
    with st.container(key="door_card"):
        st.markdown("#### Electronic Door Lock")
        st.write(f"Current Lock: **{('LOCKED' if st.session_state.door_locked else 'UNLOCKED')}**")
        d1, d2 = st.columns(2, gap="small")
        with d1:
            if st.button("Unlock Door", key="door_unlock"):
                st.session_state.door_locked = False
                send_cmd("DOOR", "UNLOCK")
        with d2:
            if st.button("Lock Door", key="door_lock"):
                st.session_state.door_locked = True
                send_cmd("DOOR", "LOCK")

# 3. Security (Intruder Alarm / Caps Mode) Control
with c3:
    with st.container(key="alarm_card"):
        st.markdown("#### Intruder Alarm Mode")
        st.write(f"Current Mode: **{('ARMED' if st.session_state.caps_mode else 'DISARMED')}**")
        a1, a2 = st.columns(2, gap="small")
        with a1:
            if st.button("Arm Alarm", key="sec_arm"):
                st.session_state.caps_mode = True
                send_cmd("CAPS", "ARM")
        with a2:
            if st.button("Disarm Alarm", key="sec_disarm"):
                st.session_state.caps_mode = False
                st.session_state.alarm_triggered = False
                send_cmd("CAPS", "DISARM")

st.markdown("---")

# 4. Graph Section (Environment Trends) - Moved to bottom
st.markdown("<h3 style='font-family: Outfit, sans-serif;'>Environment Trends</h3>", unsafe_allow_html=True)
fig = go.Figure()
if st.session_state.time_history:
    fig.add_trace(go.Scatter(
        x=st.session_state.time_history, 
        y=st.session_state.temp_history, 
        name="Temp (°C)", 
        line=dict(color='#ef4444', width=3),
        mode='lines+markers'
    ))
    fig.add_trace(go.Scatter(
        x=st.session_state.time_history, 
        y=st.session_state.hum_history, 
        name="Hum (%)", 
        line=dict(color='#06b6d4', width=3),
        mode='lines+markers'
    ))
else:
    # Empty placeholder trace to render an empty dark chart nicely
    fig.add_trace(go.Scatter(x=[0], y=[0], name="No Data Received Yet", line=dict(color='rgba(0,0,0,0)')))

fig.update_layout(
    template="plotly_dark", 
    height=340, 
    margin=dict(l=20, r=20, t=20, b=20),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
)
st.plotly_chart(fig, use_container_width=True)

# Footer and polling update
st.markdown("---")
st.caption(f"Last UI Sync: {datetime.now().strftime('%H:%M:%S')} | Local Broker Port: {MQTT_PORT}")
time.sleep(1)
st.rerun()
