/* ==========================================================
   FIREGUARD AI - script.js FINAL MQTT ONLY
   Dashboard Realtime ESP32 + HiveMQ + Socket.IO
   Universitas Brawijaya - INNOTECH 2026
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

// ===================== STATUS AWAL =====================
temp.textContent = "--°C";
gas.textContent = "--";
flame.textContent = "OFF";

status.textContent = "MENUNGGU ESP32";
statusDesc.textContent = "Menunggu data dari HiveMQ";

prediction.textContent = "Waiting MQTT Data";
confidence.textContent = "0%";
confidenceBar.style.width = "0%";

lastTime.textContent = "--:--:--";

// ===================== CHART =====================
const ctx = document.getElementById("sensorChart").getContext("2d");

const labels = [];
const tempData = [];
const gasData = [];

const sensorChart = new Chart(ctx,{
    type:"line",
    data:{
        labels,
        datasets:[
            {
                label:"Temperature (°C)",
                data:tempData,
                borderColor:"#ff4444",
                backgroundColor:"rgba(255,68,68,0.15)",
                fill:true,
                tension:0.35,
                borderWidth:2,
                pointRadius:3
            },
            {
                label:"MQ-2 Gas (PPM)",
                data:gasData,
                borderColor:"#00ff99",
                backgroundColor:"rgba(0,255,153,0.15)",
                fill:true,
                tension:0.35,
                borderWidth:2,
                pointRadius:3
            }
        ]
    },
    options:{
        responsive:true,
        maintainAspectRatio:false,
        animation:false,
        plugins:{
            legend:{
                labels:{color:"#ffffff"}
            }
        },
        scales:{
            x:{
                ticks:{color:"#cccccc"},
                grid:{color:"#333333"}
            },
            y:{
                beginAtZero:true,
                ticks:{color:"#cccccc"},
                grid:{color:"#333333"}
            }
        }
    }
});

// ===================== UPDATE CHART =====================
function updateChart(data){

    labels.push(data.time);
    tempData.push(Number(data.temperature));
    gasData.push(Number(data.gas));

    if(labels.length>20){
        labels.shift();
        tempData.shift();
        gasData.shift();
    }

    sensorChart.update();

}

// ===================== UPDATE STATUS =====================
function updateStatus(data){

    status.textContent = data.status;
    prediction.textContent = data.prediction;
    confidence.textContent = data.confidence + "%";
    confidenceBar.style.width = data.confidence + "%";

    statusCard.classList.remove("alarm");

    if(data.status==="AMAN"){

        statusCard.style.background="#0f5132";
        statusDesc.textContent="Lingkungan Aman";

        prediction.style.color="#00ff88";
        decisionText.style.color="#00ff88";
        decisionText.textContent="Tidak Terjadi Kebakaran";

        confidenceBar.style.background="#00ff88";

    }

    else if(data.status==="WASPADA"){

        statusCard.style.background="#8a6500";
        statusDesc.textContent="Gas atau Suhu Meningkat";

        prediction.style.color="#ffd54f";
        decisionText.style.color="#ffd54f";
        decisionText.textContent="Potensi Kebakaran";

        confidenceBar.style.background="#ffd54f";

    }

    else if(data.status==="KEBAKARAN"){

        statusCard.style.background="#7b0000";
        statusCard.classList.add("alarm");

        statusDesc.textContent="KEBAKARAN TERDETEKSI";

        prediction.style.color="#ff4040";
        decisionText.style.color="#ff4040";
        decisionText.textContent="🔥 FIRE ACCIDENT";

        confidenceBar.style.background="#ff4040";

        startAlarm();

    }

}

// ===================== UPDATE CAMERA =====================
function updateCamera(cameraUrl=""){

    if(!cameraPreview) return;

    if(cameraUrl){

        cameraPreview.innerHTML = `
            <img src="${cameraUrl}?t=${Date.now()}"
                 alt="ESP32-CAM"
                 style="
                    width:100%;
                    height:100%;
                    object-fit:cover;
                    border-radius:14px;
                 ">
        `;

    }else{

        cameraPreview.innerHTML = `
            <div class="camera-placeholder">
                <h2>📷 ESP32-CAM</h2>
                <p>WAITING FOR LIVE STREAM...</p>
            </div>
        `;

    }

}

// Tampilkan placeholder pertama kali
updateCamera();

// ===================== UPDATE DASHBOARD =====================
function updateDashboard(data){

    temp.textContent = data.temperature + "°C";
    gas.textContent = data.gas;
    flame.textContent = data.flame ? "ON" : "OFF";
    lastTime.textContent = data.time;

    updateStatus(data);
    updateChart(data);
    addLog(data);

    if(data.camera_url){
        updateCamera(data.camera_url);
    }

}

// ===================== FLASH ALARM =====================
let alarmRunning=false;

function startAlarm(){

    if(alarmRunning) return;

    alarmRunning=true;

    let count=0;

    const flash=setInterval(()=>{

        document.body.classList.toggle("danger-bg");

        count++;

        if(count>=10){

            clearInterval(flash);

            document.body.classList.remove("danger-bg");

            alarmRunning=false;

        }

    },300);

}

// ===================== EVENT LOG =====================
function addLog(data){

    const row=document.createElement("tr");

    let cls="safe";

    if(data.status==="WASPADA") cls="warning";
    if(data.status==="KEBAKARAN") cls="danger";

    row.innerHTML=`
        <td>${data.time}</td>
        <td>${data.gas}</td>
        <td>${data.temperature}°C</td>
        <td>${data.flame ? "ON":"OFF"}</td>
        <td class="${cls}">${data.status}</td>
    `;

    logBody.prepend(row);

    while(logBody.rows.length>15){
        logBody.deleteRow(logBody.rows.length-1);
    }

}

// ===================== SOCKET MQTT =====================
socket.on("connect",()=>{

    console.log("🟢 Dashboard Connected");

});

socket.on("disconnect",()=>{

    console.log("🔴 Dashboard Disconnected");

    status.textContent="OFFLINE";
    statusDesc.textContent="Koneksi ke Flask terputus.";

});

socket.on("sensor_update",(data)=>{

    console.log("📡 DATA MQTT :",data);

    updateDashboard(data);

});

// ===================== REFRESH CAMERA =====================
const refreshBtn=document.getElementById("refreshCamera");

if(refreshBtn){

    refreshBtn.addEventListener("click",()=>{

        cameraPreview.innerHTML=`
            <div class="camera-placeholder">
                <h2>📡 CONNECTING...</h2>
                <p>Menghubungkan ke ESP32-CAM...</p>
            </div>
        `;

        setTimeout(()=>{
            updateCamera();
        },1500);

    });

}

// ===================== TELEGRAM =====================
const telegramButton=document.getElementById("telegramButton");

if(telegramButton){

    telegramButton.addEventListener("click",()=>{

        socket.emit("telegram_alert");

        alert("📱 Telegram Alert dikirim.");

    });

}

// ===================== OWNER CONFIRM =====================
const ownerConfirm=document.getElementById("ownerConfirm");

if(ownerConfirm){

    ownerConfirm.addEventListener("click",()=>{

        socket.emit("owner_confirmation",{
            confirmation:true,
            time:new Date().toLocaleTimeString("id-ID")
        });

        alert("✅ Konfirmasi kebakaran dikirim.");

    });

}

// ===================== FIRE DEPARTMENT =====================
const fireButton=document.getElementById("fireDepartment");

if(fireButton){

    fireButton.addEventListener("click",()=>{

        socket.emit("fire_department");

        alert("🚒 Permintaan bantuan dikirim.");

    });

}

console.log("🔥 FIREGUARD AI MQTT Dashboard Ready");
console.log("Waiting MQTT Topic : fireguard/sensor");