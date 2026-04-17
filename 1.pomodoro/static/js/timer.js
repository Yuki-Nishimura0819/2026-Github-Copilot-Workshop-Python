const state = {
  mode: "idle",
  remaining: 0,
  workDuration: 1500,
  breakDuration: 300,
  timerId: null,
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

function baseDuration(mode) {
  if (mode === "break") {
    return state.breakDuration;
  }
  return state.workDuration;
}

function renderTimer() {
  timeDisplay.textContent = formatTime(state.remaining);
  statusText.textContent = modeText(state.mode);
  statusText.style.color = modeColor(state.mode);

  const total = Math.max(1, baseDuration(state.mode));
  const progress = Math.max(0, Math.min(100, ((total - state.remaining) / total) * 100));
  ringWrap.style.setProperty("--progress", progress.toFixed(2));
  ringWrap.style.setProperty("--ring-color", modeColor(state.mode));
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

async function refreshStats() {
  try {
    const stats = await api("/api/stats/today");
    const sessions = Number(stats.sessions || 0);
    const totalFocusTime = Number(stats.total_focus_time || 0);
    const mins = Math.floor(totalFocusTime / 60);

    sessionsValue.textContent = String(sessions);
    focusMinutesValue.textContent = `${mins}分`;
  } catch (error) {
    setError(error.message);
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

  state.timerId = window.setInterval(async () => {
    try {
      const data = await api("/api/timer/tick", { method: "POST" });
      applyApiState(data);

      if (data.remaining === 0) {
        if (data.state === "working") {
          const breakState = await api("/api/timer/start-break", { method: "POST" });
          applyApiState(breakState);
          await refreshStats();
        } else {
          stopLoop();
        }
      }
    } catch (error) {
      stopLoop();
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
  await refreshState();
  if (state.mode === "working" || state.mode === "break") {
    startLoop();
  }
  await refreshStats();
}

void init();
