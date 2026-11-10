let selectedService = null;
let isRunning = false;

const serviceNames = {
  followers: "Followers",
  hearts: "Hearts",
  comments_hearts: "Comments Hearts",
  views: "Views",
  shares: "Shares",
  favorites: "Favorites",
  live_stream: "Live Stream"
};

function renderServices(services) {
  const grid = document.getElementById("servicesGrid");
  if (!services || Object.keys(services).length === 0) {
    grid.innerHTML = '<p class="hint">Pulsa “Comprobar servicios” para ver cuáles están disponibles</p>';
    return;
  }

  grid.innerHTML = "";
  for (const [key, status] of Object.entries(services)) {
    const item = document.createElement("div");
    item.className = `service-item ${status === "offline" ? "offline" : ""}`;
    if (selectedService === key) item.classList.add("selected");
    item.dataset.key = key;

    item.innerHTML = `
      <div class="name">${serviceNames[key] || key}</div>
      <div class="badge ${status}">${status === "online" ? "ONLINE" : "OFFLINE"}</div>
    `;

    if (status === "online") {
      item.onclick = () => selectService(key);
    }
    grid.appendChild(item);
  }
}

function selectService(key) {
  selectedService = key;
  document.querySelectorAll(".service-item").forEach(el => {
    el.classList.toggle("selected", el.dataset.key === key);
  });
  updateButtons();
}

function updateButtons() {
  const hasUrl = document.getElementById("videoUrl").value.trim().length > 10;
  document.getElementById("btnStart").disabled = !(selectedService && hasUrl && !isRunning);
  document.getElementById("btnStop").disabled = !isRunning;
  document.getElementById("btnCheck").disabled = isRunning;
}

async function checkServices() {
  const btn = document.getElementById("btnCheck");
  btn.disabled = true;
  btn.textContent = "Abriendo Chrome...";

  try {
    const res = await fetch("/api/check-services", { method: "POST" });
    const data = await res.json();
    if (data.ok) {
      renderServices(data.services);
    } else {
      alert(data.error || "Error al comprobar servicios");
    }
  } catch (e) {
    alert("Error de conexión con el servidor");
  } finally {
    btn.textContent = "Comprobar servicios";
    updateButtons();
  }
}

async function startBot() {
  const videoUrl = document.getElementById("videoUrl").value.trim();
  if (!selectedService || !videoUrl) return;

  try {
    const res = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ service: selectedService, video_url: videoUrl })
    });
    const data = await res.json();
    if (!data.ok) {
      alert(data.error || "No se pudo iniciar");
    }
  } catch (e) {
    alert("Error de conexión");
  }
}

async function stopBot() {
  await fetch("/api/stop", { method: "POST" });
}

async function closeBrowser() {
  await fetch("/api/close-browser", { method: "POST" });
  selectedService = null;
  renderServices({});
  updateButtons();
}

function updateStatus(data) {
  isRunning = data.running;
  const dot = document.getElementById("statusDot");
  const text = document.getElementById("statusText");

  text.textContent = data.message || "Listo";
  dot.className = "dot " + (data.running ? "running" : "online");

  // Logs
  const logsEl = document.getElementById("logs");
  logsEl.innerHTML = (data.logs || []).map(l => `<div>${l}</div>`).join("");
  logsEl.scrollTop = logsEl.scrollHeight;

  // Services (solo si ya se comprobaron)
  if (data.services && Object.keys(data.services).length > 0) {
    renderServices(data.services);
  }

  updateButtons();
}

// Polling cada 1.5s
setInterval(async () => {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    updateStatus(data);
  } catch (e) {}
}, 1500);

// Input change
document.getElementById("videoUrl").addEventListener("input", updateButtons);

updateButtons();
