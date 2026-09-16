/* ==========================================================
   FIREGUARD AI - script.js (FINAL VERSION)
   Dashboard Realtime ESP32 + MQTT + Computer Vision
   ========================================================== */

// ===================== SOCKET.IO =====================
const socket = io();

// ===================== HTML ELEMENT =====================
const temp = document.getElementById("temp");
const gas = document.getElementById("gas");
const flame = document.getElementById("flame");

const status = document.getElementById("status");
const statusDesc = document.getElementById("statusDesc");
const statusCard = document.getElementById("statusCard");

const prediction = document.getElementById("prediction");
const confidence = document.getElementById("confidence");
const confidenceBar = document.getElementById("confidenceBar");
const decisionText = document.getElementById("decisionText");

const lastTime = document.getElementById("lastTime");
const logBody = document.getElementById("logBody");

const cameraPreview = document.getElementById("cameraPreview");

// ===================== CHART =====================
const ctx = document.getElementById("sensorChart").getContext("2d");

const labels = [];
const tempData = [];
const gasData = [];

const sensorChart = new Chart(ctx, {
    type: "line",
    data: {
        labels: labels,
        datasets: [
            {
                label: "Temperature (°C)",
                data: tempData,
                borderColor: "#ff4444",
                backgroundColor: "rgba(255,68,68,0.15)",
                fill: true,
                tension: 0.4,
            },
            {
                label: "MQ-2 Gas (PPM)",
                data: gasData,
                borderColor: "#00ff99",
                backgroundColor: "rgba(0,255,153,0.15)",
                fill: true,
                tension: 0.4,
            },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: "#ffffff",
                },
            },
        },
        scales: {
            x: {
                ticks: { color: "#cccccc" },
                grid: { color: "#333333" },
            },
            y: {
                ticks: { color: "#cccccc" },
                grid: { color: "#333333" },
            },
        },
    },
});

// ===================== UPDATE DASHBOARD =====================
function updateDashboard(data) {
    temp.innerHTML = data.temperature + "°C";
    gas.innerHTML = data.gas;
    flame.innerHTML = data.flame ? "ON" : "OFF";
    lastTime.innerHTML = data.time;

    labels.push(data.time);
    tempData.push(data.temperature);
    gasData.push(data.gas);

    if (labels.length > 15) {
        labels.shift();
        tempData.shift();
        gasData.shift();
    }

    sensorChart.update();

    updateStatus(data);
    addLog(data);
}

// ===================== STATUS =====================
function updateStatus(data) {
    status.innerHTML = data.status;
    prediction.innerHTML = data.prediction;
    confidence.innerHTML = data.confidence + "%";
    confidenceBar.style.width = data.confidence + "%";

    statusCard.classList.remove("alarm");

    if (data.status === "AMAN") {
        statusCard.style.background = "#0f5132";
        statusDesc.innerHTML = "Lingkungan Aman";

        decisionText.innerHTML = "Tidak Terjadi Kebakaran";
        decisionText.style.color = "#00ff88";

        prediction.style.color = "#00ff88";
        confidenceBar.style.background = "#00ff88";
    }

    else if (data.status === "WASPADA") {
        statusCard.style.background = "#8a6500";
        statusDesc.innerHTML = "Gas atau Suhu Meningkat";

        decisionText.innerHTML = "Potensi Kebakaran";
        decisionText.style.color = "#ffd54f";

        prediction.style.color = "#ffd54f";
        confidenceBar.style.background = "#ffd54f";
    }

    else {
        statusCard.style.background = "#7b0000";
        statusCard.classList.add("alarm");

        statusDesc.innerHTML = "KEBAKARAN TERDETEKSI";

        decisionText.innerHTML = "🔥 FIRE ACCIDENT";
        decisionText.style.color = "#ff4040";

        prediction.style.color = "#ff4040";
        confidenceBar.style.background = "#ff4040";

        startAlarm();
    }
}

// ===================== ALARM =====================
let flashing = false;

function startAlarm() {

    if (flashing) return;

    flashing = true;

    let count = 0;

    const alarm = setInterval(() => {

        document.body.style.background =
            count % 2 === 0 ? "#2b0000" : "#090909";

        count++;

        if (count > 8) {
            clearInterval(alarm);
            document.body.style.background = "#090909";
            flashing = false;
        }

    }, 250);
}

// ===================== FIRE EVENT LOG =====================
function addLog(data) {

    const row = document.createElement("tr");

    let cls = "safe";

    if (data.status === "WASPADA") cls = "warning";
    if (data.status === "KEBAKARAN") cls = "danger";

    row.innerHTML = `
        <td>${data.time}</td>
        <td>${data.gas}</td>
        <td>${data.temperature}°C</td>
        <td>${data.flame ? "ON" : "OFF"}</td>
        <td class="${cls}">${data.status}</td>
    `;

    logBody.prepend(row);

    while (logBody.rows.length > 10) {
        logBody.deleteRow(logBody.rows.length - 1);
    }
}

// ===================== SOCKET RECEIVE =====================
socket.on("sensor_update", (data) => {
    updateDashboard(data);
});

// ===================== CAMERA REFRESH =====================
const refreshBtn = document.getElementById("refreshCamera");

if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {

        cameraPreview.src =
            "https://placehold.co/640x360/111111/ff4444?text=Refreshing+Camera";

        setTimeout(() => {

            // Ganti dengan IP ESP32-CAM nanti
            cameraPreview.src =
                "https://placehold.co/640x360/111111/ff3333?text=ESP32-CAM+LIVE";

        }, 1200);
    });
}

// ===================== TELEGRAM BUTTON =====================
const telegramButton = document.getElementById("telegramButton");

if (telegramButton) {

    telegramButton.addEventListener("click", () => {

        alert(
            "📱 FIREGUARD AI\n\n" +
            "Notifikasi Telegram berhasil dikirim (Simulasi).\n\n" +
            "Versi final akan mengirim pesan ke HP pemilik."
        );

    });

}

// ===================== OWNER CONFIRM =====================
const ownerConfirm = document.getElementById("ownerConfirm");

if (ownerConfirm) {

    ownerConfirm.addEventListener("click", () => {

        socket.emit("owner_confirmation", {
            status: "KEBAKARAN"
        });

        alert(
            "✅ Pemilik mengkonfirmasi kebakaran.\n\n" +
            "Sistem akan menghubungi pemadam kebakaran."
        );

    });

}

// ===================== FIRE DEPARTMENT BUTTON =====================
const fireButton = document.getElementById("fireDepartment");

if (fireButton) {

    fireButton.addEventListener("click", () => {

        alert(
            "🚒 FIREGUARD AI\n\n" +
            "Mengirim laporan darurat ke Pemadam Kebakaran (Simulasi)."
        );

    });

}

// ===================== DEMO MODE =====================
// Dashboard tetap hidup walaupun MQTT belum aktif.

function demoMode() {

    const demo = {
        temperature: Math.floor(Math.random() * 45) + 25,
        gas: Math.floor(Math.random() * 2200) + 400,
        flame: Math.random() > 0.85,
        status: "AMAN",
        prediction: "Cooking Activity",
        confidence: 95,
        time: new Date().toLocaleTimeString("id-ID"),
    };

    if (demo.flame || (demo.gas > 1800 && demo.temperature > 50)) {
        demo.status = "KEBAKARAN";
        demo.prediction = "Fire Accident";
        demo.confidence = 99;
    }

    else if (demo.gas > 1200 || demo.temperature > 42) {
        demo.status = "WASPADA";
        demo.prediction = "Smoke / Heat";
        demo.confidence = 88;
    }

    updateDashboard(demo);
}

// Jalankan demo hanya jika Socket belum mengirim data.
let firstData = false;

socket.on("sensor_update", () => {
    firstData = true;
});

setInterval(() => {
    if (!firstData) demoMode();
}, 3000);

// Tampilan awal
demoMode();