# ==========================================================
# FIREGUARD AI
# Smart Fire Detection & Mitigation Monitoring System
# Backend Flask + SocketIO + MQTT Ready
# Universitas Brawijaya - INNOTECH 2026
# ==========================================================

from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import random
import time
import json
import csv
import os
from datetime import datetime

import paho.mqtt.client as mqtt

# ==========================================================
# FLASK CONFIGURATION
# ==========================================================

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    socketio.run(
        app,
        host="0.0.0.0",
        port=port
    )

# ==========================================================
# HIVE MQTT CONFIGURATION
# ==========================================================

BROKER = "xxxxxxxx.s1.eu.hivemq.cloud"   # Ganti dengan Cluster HiveMQ
PORT = 8883

USERNAME = "USERNAME_HIVEMQ"             # Ganti Username HiveMQ
PASSWORD = "PASSWORD_HIVEMQ"             # Ganti Password HiveMQ

TOPIC_SENSOR = "fireguard/sensor"

# ==========================================================
# DATA LOG
# ==========================================================

DATA_FOLDER = "data"
CSV_FILE = os.path.join(DATA_FOLDER, "event_log.csv")

os.makedirs(DATA_FOLDER, exist_ok=True)

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
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
# DATA GLOBAL
# ==========================================================

sensor_data = {
    "temperature": 30,
    "gas": 800,
    "flame": False,
    "status": "AMAN",
    "prediction": "Cooking Activity",
    "confidence": 95,
    "time": datetime.now().strftime("%H:%M:%S")
}

# ==========================================================
# FIRE DECISION
# ==========================================================

def fire_decision(temp, gas, flame):

    status = "AMAN"
    prediction = "Cooking Activity"
    confidence = 95

    if flame and gas > 1800 and temp > 50:
        status = "KEBAKARAN"
        prediction = "Fire Accident"
        confidence = 99

    elif gas > 1300 or temp > 42:
        status = "WASPADA"
        prediction = "Smoke / Heat"
        confidence = 88

    return status, prediction, confidence


# ==========================================================
# SAVE LOG CSV
# ==========================================================

def save_log():

    with open(CSV_FILE, "a", newline="") as f:

        writer = csv.writer(f)

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
# ROUTE DASHBOARD
# ==========================================================

@app.route("/")
def dashboard():
    return render_template("index.html")


# ==========================================================
# SOCKET.IO DARI COMPUTER VISION
# ==========================================================

@socketio.on("cv_update")
def cv_update(data):

    sensor_data["prediction"] = data["prediction"]
    sensor_data["status"] = data["status"]
    sensor_data["confidence"] = data["confidence"]

    socketio.emit("sensor_update", sensor_data)


# ==========================================================
# KONFIRMASI PEMILIK
# ==========================================================

@socketio.on("owner_confirmation")
def owner_confirmation(data):

    print("Owner Confirmation :", data)


# ==========================================================
# MQTT CALLBACK
# ==========================================================

def on_connect(client, userdata, flags, reason_code, properties=None):

    print("MQTT Connected")

    client.subscribe(TOPIC_SENSOR)


def on_message(client, userdata, msg):

    global sensor_data

    try:

        payload = json.loads(msg.payload.decode())

        temp = payload.get("temperature", 30)
        gas = payload.get("gas", 800)
        flame = payload.get("flame", False)

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

        print(sensor_data)

    except Exception as e:
        print("MQTT Error :", e)


# ==========================================================
# MQTT THREAD
# ==========================================================

def mqtt_thread():

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    client.username_pw_set(USERNAME, PASSWORD)
    client.tls_set()

    client.on_connect = on_connect
    client.on_message = on_message

    try:

        client.connect(BROKER, PORT, 60)
        client.loop_forever()

    except Exception as e:
        print("MQTT Failed :", e)


# ==========================================================
# DEMO SENSOR (UNTUK WOKWI / TANPA MQTT)
# ==========================================================

def simulator():

    global sensor_data

    while True:

        temp = random.randint(25, 65)
        gas = random.randint(400, 2400)
        flame = random.choice([False, False, False, True])

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

        time.sleep(3)


# ==========================================================
# START SYSTEM
# ==========================================================

if __name__ == "__main__":

    print("=" * 45)
    print("🔥 FIREGUARD AI DASHBOARD")
    print("Dashboard : http://127.0.0.1:5000")
    print("=" * 45)

    DEMO_MODE = True      # True = Simulasi | False = MQTT ESP32

    if DEMO_MODE:
        threading.Thread(
            target=simulator,
            daemon=True
        ).start()
    else:
        threading.Thread(
            target=mqtt_thread,
            daemon=True
        ).start()

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True
    )