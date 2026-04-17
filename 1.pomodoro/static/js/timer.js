const state = {
  mode: "idle",
  remaining: 0,
  workDuration: 1500,
  breakDuration: 300,
  longBreakDuration: 900,
  sessionsUntilLongBreak: 4,
  timerId: null,
  statsRefreshId: null,
  soundEnabled: localStorage.getItem("soundEnabled") !== "false",
  darkMode: localStorage.getItem("darkMode") === "true",
  uiVariant: "enhanced",
};

const statusText = document.getElementById("statusText");
const timeDisplay = document.getElementById("timeDisplay");
const sessionsValue = document.getElementById("sessionsValue");
const focusMinutesValue = document.getElementById("focusMinutesValue");
const ringWrap = document.getElementById("ringWrap");
const errorMessage = document.getElementById("errorMessage");
const startButton = document.getElementById("startButton");
const resetButton = document.getElementById("resetButton");

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const secs = (seconds % 60).toString().padStart(2, "0");
  return `${mins}:${secs}`;
}

function modeText(mode) {
  if (mode === "working") {
    return "作業中";
  }
  if (mode === "break") {
    return "休憩中";
  }
  return "待機中";
}

function modeColor(mode) {
  if (mode === "working") {
    return "#e4572e";
  }
  if (mode === "break") {
    return "#0f766e";
  }
  return "#8b6d5c";
}

function blendHexColor(startHex, endHex, ratio) {
  const clamped = Math.max(0, Math.min(1, ratio));
  const start = startHex.replace("#", "");
  const end = endHex.replace("#", "");

  const sr = parseInt(start.slice(0, 2), 16);
  const sg = parseInt(start.slice(2, 4), 16);
  const sb = parseInt(start.slice(4, 6), 16);
  const er = parseInt(end.slice(0, 2), 16);
  const eg = parseInt(end.slice(2, 4), 16);
  const eb = parseInt(end.slice(4, 6), 16);

  const r = Math.round(sr + (er - sr) * clamped);
  const g = Math.round(sg + (eg - sg) * clamped);
  const b = Math.round(sb + (eb - sb) * clamped);
  return `rgb(${r}, ${g}, ${b})`;
}

function focusColorByRemainingRatio(remainingRatio) {
  const ratio = Math.max(0, Math.min(1, remainingRatio));
  if (ratio >= 0.5) {
    return blendHexColor("#3b82f6", "#facc15", (1 - ratio) / 0.5);
  }
  return blendHexColor("#facc15", "#ef4444", (0.5 - ratio) / 0.5);
}

function resolveUiVariant() {
  const query = new URLSearchParams(window.location.search).get("ui");
  if (query === "control" || query === "enhanced") {
    localStorage.setItem("uiVariant", query);
    return query;
  }

  const saved = localStorage.getItem("uiVariant");
  if (saved === "control" || saved === "enhanced") {
    return saved;
  }

  const assigned = Math.random() < 0.5 ? "control" : "enhanced";
  localStorage.setItem("uiVariant", assigned);
  return assigned;
}

function baseDuration(mode) {
  if (mode === "break") {
    return state.breakDuration;
  }
  return state.workDuration;
}

function renderTimer() {
  timeDisplay.textContent = formatTime(state.remaining);
  statusText.textContent = modeText(state.mode);

  const total = Math.max(1, baseDuration(state.mode));
  const remainingRatio = Math.max(0, Math.min(1, state.remaining / total));
  const elapsedProgress = Math.max(0, Math.min(100, ((total - state.remaining) / total) * 100));

  if (state.uiVariant === "enhanced" && state.mode === "working") {
    const focusColor = focusColorByRemainingRatio(remainingRatio);
    ringWrap.style.setProperty("--progress", (remainingRatio * 100).toFixed(2));
    ringWrap.style.setProperty("--ring-color", focusColor);
    statusText.style.color = focusColor;
    document.body.classList.add("focus-active");
  } else {
    ringWrap.style.setProperty("--progress", elapsedProgress.toFixed(2));
    ringWrap.style.setProperty("--ring-color", modeColor(state.mode));
    statusText.style.color = modeColor(state.mode);
    document.body.classList.remove("focus-active");
  }
}

function setError(message) {
  errorMessage.textContent = message || "";
}

function applyApiState(payload) {
  state.mode = payload.state || "idle";
  state.remaining = Number.isFinite(payload.remaining) ? payload.remaining : 0;

  if (state.mode === "working") {
    state.workDuration = Math.max(state.workDuration, state.remaining);
  }
  if (state.mode === "break") {
    state.breakDuration = Math.max(state.breakDuration, state.remaining);
  }

  renderTimer();
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "APIエラーが発生しました");
  }
  return data;
}

// Phase 6: Sound notification
function playNotificationSound(type = "complete") {
  if (!state.soundEnabled) {
    return;
  }
  try {
    // Use Web Audio API to generate simple beep tone
    const context = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = context.createOscillator();
    const gainNode = context.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(context.destination);

    if (type === "complete") {
      oscillator.frequency.value = 800;
      gainNode.gain.setValueAtTime(0.3, context.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.5);
      oscillator.start(context.currentTime);
      oscillator.stop(context.currentTime + 0.5);
    } else if (type === "break") {
      oscillator.frequency.value = 600;
      gainNode.gain.setValueAtTime(0.2, context.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.3);
      oscillator.start(context.currentTime);
      oscillator.stop(context.currentTime + 0.3);
    }
  } catch (e) {
    console.log("Sound notification not available:", e);
  }
}

// Phase 6: Dark mode toggle
function toggleDarkMode() {
  state.darkMode = !state.darkMode;
  localStorage.setItem("darkMode", state.darkMode.toString());
  document.documentElement.setAttribute("data-theme", state.darkMode ? "dark" : "light");
}

// Initialize dark mode on load
function initDarkMode() {
  document.documentElement.setAttribute("data-theme", state.darkMode ? "dark" : "light");
}

function initUiVariant() {
  state.uiVariant = resolveUiVariant();
  document.body.dataset.uiVariant = state.uiVariant;
}

async function refreshStats() {
  try {
    const stats = await api("/api/stats/today");
    const sessions = Number(stats.sessions || 0);
    const formatTime = stats.formatted_time || `${Math.floor((stats.total_focus_time || 0) / 60)}分`;

    sessionsValue.textContent = String(sessions);
    focusMinutesValue.textContent = formatTime;
  } catch (error) {
    setError(error.message);
  }
}

async function startStatsRefresh() {
  if (state.statsRefreshId) {
    return;
  }
  // Refresh stats every 5 seconds
  state.statsRefreshId = window.setInterval(async () => {
    await refreshStats();
  }, 5000);
}

function stopStatsRefresh() {
  if (state.statsRefreshId) {
    window.clearInterval(state.statsRefreshId);
    state.statsRefreshId = null;
  }
}

async function refreshState() {
  try {
    const data = await api("/api/timer/state");
    applyApiState(data);
    setError("");
  } catch (error) {
    setError(error.message);
  }
}

async function loadConfig() {
  try {
    const config = await api("/api/config");
    state.workDuration = config.work_duration || 1500;
    state.breakDuration = config.break_duration || 300;
    state.longBreakDuration = config.long_break_duration || 900;
    state.sessionsUntilLongBreak = config.sessions_until_long_break || 4;
  } catch (error) {
    console.warn("Failed to load config:", error);
  }
}

function stopLoop() {
  if (state.timerId) {
    window.clearInterval(state.timerId);
    state.timerId = null;
  }
}

function startLoop() {
  if (state.timerId) {
    return;
  }

  startStatsRefresh();

  state.timerId = window.setInterval(async () => {
    try {
      const data = await api("/api/timer/tick", { method: "POST" });
      applyApiState(data);

      if (data.remaining === 0) {
        playNotificationSound("complete");
        if (data.state === "working") {
          const breakState = await api("/api/timer/start-break", { method: "POST" });
          applyApiState(breakState);
          playNotificationSound("break");
          await refreshStats();
        } else {
          stopLoop();
          stopStatsRefresh();
        }
      }
    } catch (error) {
      stopLoop();
      stopStatsRefresh();
      setError(error.message);
    }
  }, 1000);
}

async function startWork() {
  try {
    const data = await api("/api/timer/start-work", { method: "POST" });
    state.workDuration = Math.max(data.remaining || 0, 1);
    applyApiState(data);
    setError("");
    startLoop();
  } catch (error) {
    setError(error.message);
  }
}

async function resetTimer() {
  try {
    const data = await api("/api/timer/reset", { method: "POST" });
    stopLoop();
    stopStatsRefresh();
    state.workDuration = Math.max(data.remaining || state.workDuration, 1);
    applyApiState(data);
    await refreshStats();
    setError("");
  } catch (error) {
    setError(error.message);
  }
}

startButton.addEventListener("click", () => {
  void startWork();
});

resetButton.addEventListener("click", () => {
  void resetTimer();
});

async function init() {
  initUiVariant();
  initDarkMode();
  await loadConfig();
  await refreshState();
  if (state.mode === "working" || state.mode === "break") {
    startLoop();
  }
  await refreshStats();
}

void init();
