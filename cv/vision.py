# ==========================================================
# FIREGUARD AI - Computer Vision Engine
# ESP32-CAM + OpenCV + SocketIO
# ==========================================================

import cv2
import numpy as np
import socketio

# ==========================================================
# SOCKET.IO CLIENT
# ==========================================================

sio = socketio.Client()

try:
    sio.connect("http://127.0.0.1:5000")
    print("Dashboard Connected")
except:
    print("Dashboard Offline")

# ==========================================================
# ESP32-CAM STREAM
# ==========================================================

ESP32_CAM_URL = "http://192.168.1.150:81/stream"
cap = cv2.VideoCapture(ESP32_CAM_URL)

# Jika tidak ada ESP32-CAM gunakan webcam laptop
if not cap.isOpened():
    print("ESP32-CAM tidak ditemukan, menggunakan Webcam Laptop.")
    cap = cv2.VideoCapture(0)

# ==========================================================
# DETEKSI API (HSV)
# ==========================================================

def detect_fire(frame):

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_fire = np.array([0,120,150])
    upper_fire = np.array([35,255,255])

    mask = cv2.inRange(hsv, lower_fire, upper_fire)

    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.GaussianBlur(mask,(7,7),0)

    contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

    area = 0
    fire_detected = False

    for cnt in contours:

        if cv2.contourArea(cnt) > 1000:

            fire_detected = True
            area = max(area, cv2.contourArea(cnt))

            x,y,w,h = cv2.boundingRect(cnt)

            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,0,255),2)
            cv2.putText(frame,"FIRE",(x,y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,(0,0,255),2)

    return fire_detected, area, frame

# ==========================================================
# DETEKSI ASAP
# ==========================================================

def detect_smoke(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray,(15,15),0)

    _, thresh = cv2.threshold(blur,160,255,cv2.THRESH_BINARY)

    contours,_ = cv2.findContours(thresh,
                                  cv2.RETR_EXTERNAL,
                                  cv2.CHAIN_APPROX_SIMPLE)

    smoke_detected = False
    smoke_area = 0

    for cnt in contours:

        if cv2.contourArea(cnt) > 2500:

            smoke_detected = True
            smoke_area = max(smoke_area, cv2.contourArea(cnt))

            x,y,w,h = cv2.boundingRect(cnt)

            cv2.rectangle(frame,(x,y),(x+w,y+h),(180,180,180),2)

            cv2.putText(frame,"SMOKE",(x,y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,(200,200,200),2)

    return smoke_detected, smoke_area, frame

# ==========================================================
# AI DECISION
# ==========================================================

def ai_decision(fire, smoke, fire_area, smoke_area):

    prediction = "Cooking Activity"
    status = "AMAN"
    confidence = 95

    if fire:
        prediction = "Fire Accident"
        status = "KEBAKARAN"

        confidence = min(
            99,
            int(90 + fire_area / 1500)
        )

    elif smoke:
        prediction = "Smoke / Heat"
        status = "WASPADA"

        confidence = min(
            90,
            int(70 + smoke_area / 2500)
        )

    return prediction, status, confidence

# ==========================================================
# MAIN LOOP
# ==========================================================

print("Computer Vision Running...")

while True:

    ret, frame = cap.read()

    if not ret:
        continue

    frame = cv2.resize(frame,(960,540))

    fire, fire_area, frame = detect_fire(frame)

    smoke, smoke_area, frame = detect_smoke(frame)

    prediction, status, confidence = ai_decision(
        fire,
        smoke,
        fire_area,
        smoke_area
    )

    # Dashboard Update
    sio.emit("cv_update",{
        "prediction": prediction,
        "status": status,
        "confidence": confidence
    })

    # Panel AI
    color = (0,255,0)

    if status == "WASPADA":
        color = (0,255,255)

    if status == "KEBAKARAN":
        color = (0,0,255)

    cv2.rectangle(frame,(10,10),(380,120),(30,30,30),-1)

    cv2.putText(frame,"FIREGUARD AI",
                (20,35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,(0,140,255),2)

    cv2.putText(frame,f"Prediction : {prediction}",
                (20,65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,color,2)

    cv2.putText(frame,f"Status : {status}",
                (20,90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,color,2)

    cv2.putText(frame,f"Confidence : {confidence}%",
                (20,115),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,(255,255,255),2)

    cv2.imshow("FIREGUARD AI - Computer Vision", frame)

    key = cv2.waitKey(1)

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

try:
    sio.disconnect()
except:
    pass