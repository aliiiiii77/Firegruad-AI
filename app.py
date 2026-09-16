# ==========================================================
# FIREGUARD AI v4.0 FINAL (RAILWAY READY)
# Smart Fire Detection & Mitigation Monitoring System
# ESP32 + HiveMQ Cloud + Flask + Socket.IO
# Universitas Brawijaya - INNOTECH 2026
# ==========================================================

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from dotenv import load_dotenv

import paho.mqtt.client as mqtt
import threading
import ssl
import json
import csv
import os
import time
from datetime import datetime

# ==========================================================
# LOAD ENVIRONMENT
# ==========================================================

load_dotenv()

# ==========================================================
# FLASK CONFIG
# ==========================================================

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fireguard2026")

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)
# ==========================================================
# MQTT CONFIG (Railway Environment Variables)
# ==========================================================

BROKER = os.getenv(
    "BROKER",
    "663b70db43fe458b9098b4d55f4d9169.s1.eu.hivemq.cloud"
)

MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "FIREGUARD")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "FIREGUARD77")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "fireguard/sensor")

# ==========================================================
# DATA FOLDER
# ==========================================================

DATA_FOLDER = "data"
CSV_FILE = os.path.join(DATA_FOLDER, "event_log.csv")

os.makedirs(DATA_FOLDER, exist_ok=True)

if not os.path.exists(CSV_FILE):

    with open(CSV_FILE, "w", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            "time",
            "temperature",
            "gas",
            "flame",
            "status",
            "prediction",
            "confidence"
        ])

# ==========================================================
# GLOBAL SENSOR DATA
# ==========================================================

sensor_data = {
    "temperature": "--",
    "gas": "--",
    "flame": False,
    "status": "MENUNGGU ESP32",
    "prediction": "Waiting MQTT Data",
    "confidence": 0,
    "time": "--:--:--"
}

# ==========================================================
# FIRE DECISION ENGINE
# ==========================================================

def fire_decision(temp, gas, flame):

    status = "AMAN"
    prediction = "Cooking Activity"
    confidence = 95

    if flame and gas >= 1800 and temp >= 50:
        status = "KEBAKARAN"
        prediction = "Fire Accident"
        confidence = 99

    elif flame or gas >= 1300 or temp >= 42:
        status = "WASPADA"
        prediction = "Smoke / Heat"
        confidence = 88

    return status, prediction, confidence

# ==========================================================
# SAVE CSV LOG
# ==========================================================

def save_log():

    with open(CSV_FILE, "a", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            sensor_data["time"],
            sensor_data["temperature"],
            sensor_data["gas"],
            sensor_data["flame"],
            sensor_data["status"],
            sensor_data["prediction"],
            sensor_data["confidence"]
        ])

# ==========================================================
# ROUTES
# ==========================================================

@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/api/sensor")
def api_sensor():
    return jsonify(sensor_data)


@app.route("/api/log")
def api_log():

    logs = []

    try:
        with open(CSV_FILE, newline="") as file:
            reader = csv.DictReader(file)
            logs = list(reader)[-30:]
    except:
        pass

    return jsonify(logs)

# ==========================================================
# SOCKET EVENTS
# ==========================================================

@socketio.on("owner_confirmation")
def owner_confirmation(data):

    print("\n==============================")
    print("OWNER CONFIRMATION RECEIVED")
    print(data)
    print("==============================\n")


@socketio.on("telegram_alert")
def telegram_alert():

    print("\nTelegram Alert Requested\n")


@socketio.on("fire_department")
def fire_department():

    print("\nEmergency Fire Department Requested\n")


@socketio.on("cv_update")
def cv_update(data):

    sensor_data["prediction"] = data.get(
        "prediction",
        sensor_data["prediction"]
    )

    sensor_data["status"] = data.get(
        "status",
        sensor_data["status"]
    )

    sensor_data["confidence"] = data.get(
        "confidence",
        sensor_data["confidence"]
    )

    socketio.emit("sensor_update", sensor_data)

# ==========================================================
# MQTT CALLBACKS
# ==========================================================

def on_connect(client, userdata, flags, reason_code, properties=None):

    if reason_code == 0:

        print("\n==========================================")
        print("MQTT CONNECTED TO HIVEMQ CLOUD")
        print("Broker :", BROKER)
        print("Topic  :", MQTT_TOPIC)
        print("==========================================\n")

        client.subscribe(MQTT_TOPIC)

    else:

        print("MQTT FAILED :", reason_code)


def on_message(client, userdata, msg):

    global sensor_data

    try:

        payload = json.loads(msg.payload.decode())

        temp = float(payload.get("temperature", 0))
        gas = int(payload.get("gas", 0))
        flame = bool(payload.get("flame", False))

        status, prediction, confidence = fire_decision(
            temp,
            gas,
            flame
        )

        sensor_data.update({
            "temperature": temp,
            "gas": gas,
            "flame": flame,
            "status": status,
            "prediction": prediction,
            "confidence": confidence,
            "time": datetime.now().strftime("%H:%M:%S")
        })

        save_log()

        socketio.emit("sensor_update", sensor_data)

        print("\n========== MQTT DATA ==========")
        print(sensor_data)
        print("===============================\n")

    except Exception as err:

        print("MQTT ERROR :", err)

# ==========================================================
# MQTT THREAD (AUTO RECONNECT)
# ==========================================================

mqtt_started = False

def mqtt_thread():

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    client.username_pw_set(
        MQTT_USERNAME,
        MQTT_PASSWORD
    )

    client.tls_set(
        tls_version=ssl.PROTOCOL_TLS_CLIENT
    )

    client.on_connect = on_connect
    client.on_message = on_message

    while True:

        try:

            print("Connecting HiveMQ Cloud...")

            client.connect(
                BROKER,
                MQTT_PORT,
                keepalive=60
            )

            client.loop_forever()

        except Exception as err:

            print("MQTT CONNECTION LOST")
            print(err)

            time.sleep(5)


def start_mqtt():

    global mqtt_started

    if mqtt_started:
        return

    mqtt_started = True

    threading.Thread(
        target=mqtt_thread,
        daemon=True
    ).start()

# ==========================================================
# START MQTT
# ==========================================================

start_mqtt()

# ==========================================================
# MAIN SERVER
# ==========================================================

if __name__ == "__main__":

    print("=" * 55)
    print("🔥 FIREGUARD AI DASHBOARD v4.0 (RAILWAY READY)")
    print("Dashboard Port :", os.getenv("PORT", "5000"))
    print("Broker         :", BROKER)
    print("Topic          :", MQTT_TOPIC)
    print("=" * 55)

    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=False,
        allow_unsafe_werkzeug=True
    )