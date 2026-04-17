const state = {
  mode: "idle",
  remaining: 0,
  workDuration: 1500,
  breakDuration: 300,
  longBreakDuration: 900,
  sessionsUntilLongBreak: 4,
  timerId: null,
  statsRefreshId: null,
  soundSettings: {
    start: localStorage.getItem("soundStartEnabled") !== "false",
    end: localStorage.getItem("soundEndEnabled") !== "false",
    tick: localStorage.getItem("soundTickEnabled") === "true",
  },
  theme: localStorage.getItem("theme") || "light",
};

const statusText = document.getElementById("statusText");
const timeDisplay = document.getElementById("timeDisplay");
const sessionsValue = document.getElementById("sessionsValue");
const focusMinutesValue = document.getElementById("focusMinutesValue");
const levelValue = document.getElementById("levelValue");
const streakValue = document.getElementById("streakValue");
const xpValue = document.getElementById("xpValue");
const badgeList = document.getElementById("badgeList");
const weekSummary = document.getElementById("weekSummary");
const monthSummary = document.getElementById("monthSummary");
const weekChart = document.getElementById("weekChart");
const monthChart = document.getElementById("monthChart");
const ringWrap = document.getElementById("ringWrap");
const errorMessage = document.getElementById("errorMessage");
const startButton = document.getElementById("startButton");
const resetButton = document.getElementById("resetButton");
const darkModeBtn = document.getElementById("darkModeBtn");
const themeIcon = document.getElementById("themeIcon");
const settingsBtn = document.getElementById("settingsBtn");
const settingsModal = document.getElementById("settingsModal");
const closeSettingsBtn = document.getElementById("closeSettingsBtn");
const cancelSettingsBtn = document.getElementById("cancelSettingsBtn");
const applySettingsBtn = document.getElementById("applySettingsBtn");
const workDurationInput = document.getElementById("workDurationInput");
const breakDurationInput = document.getElementById("breakDurationInput");
const longBreakDurationInput = document.getElementById("longBreakDurationInput");
const sessionsUntilLongBreakInput = document.getElementById("sessionsUntilLongBreakInput");
const themeSelect = document.getElementById("themeSelect");
const startSoundCheckbox = document.getElementById("startSoundCheckbox");
const endSoundCheckbox = document.getElementById("endSoundCheckbox");
const tickSoundCheckbox = document.getElementById("tickSoundCheckbox");

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

// Phase 6: Sound notification
function playNotificationSound(type = "end") {
  if (type === "start" && !state.soundSettings.start) {
    return;
  }
  if (type === "end" && !state.soundSettings.end) {
    return;
  }
  if (type === "tick" && !state.soundSettings.tick) {
    return;
  }
  try {
    const context = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = context.createOscillator();
    const gainNode = context.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(context.destination);

    if (type === "start") {
      oscillator.frequency.value = 660;
      gainNode.gain.setValueAtTime(0.16, context.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.2);
      oscillator.start(context.currentTime);
      oscillator.stop(context.currentTime + 0.2);
    } else if (type === "tick") {
      oscillator.frequency.value = 420;
      gainNode.gain.setValueAtTime(0.04, context.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.08);
      oscillator.start(context.currentTime);
      oscillator.stop(context.currentTime + 0.08);
    } else {
      oscillator.frequency.value = 800;
      gainNode.gain.setValueAtTime(0.25, context.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.5);
      oscillator.start(context.currentTime);
      oscillator.stop(context.currentTime + 0.5);
    }
  } catch (e) {
    console.log("Sound notification not available:", e);
  }
}

function applyTheme(theme) {
  state.theme = ["light", "dark", "focus"].includes(theme) ? theme : "light";
  localStorage.setItem("theme", state.theme);
  document.documentElement.setAttribute("data-theme", state.theme);
  if (themeIcon) {
    themeIcon.textContent = state.theme === "dark" ? "🌙" : state.theme === "focus" ? "🎯" : "☀️";
  }
  if (themeSelect) {
    themeSelect.value = state.theme;
  }
}

function cycleTheme() {
  const currentIndex = ["light", "dark", "focus"].indexOf(state.theme);
  const nextIndex = (currentIndex + 1) % 3;
  applyTheme(["light", "dark", "focus"][nextIndex]);
}

function syncSoundSettingsUI() {
  startSoundCheckbox.checked = state.soundSettings.start;
  endSoundCheckbox.checked = state.soundSettings.end;
  tickSoundCheckbox.checked = state.soundSettings.tick;
}

function applySoundSettingsFromUI() {
  state.soundSettings.start = startSoundCheckbox.checked;
  state.soundSettings.end = endSoundCheckbox.checked;
  state.soundSettings.tick = tickSoundCheckbox.checked;
  localStorage.setItem("soundStartEnabled", String(state.soundSettings.start));
  localStorage.setItem("soundEndEnabled", String(state.soundSettings.end));
  localStorage.setItem("soundTickEnabled", String(state.soundSettings.tick));
}

function openSettingsModal() {
  workDurationInput.value = String(state.workDuration);
  breakDurationInput.value = String(state.breakDuration);
  longBreakDurationInput.value = String(state.longBreakDuration);
  sessionsUntilLongBreakInput.value = String(state.sessionsUntilLongBreak);
  themeSelect.value = state.theme;
  syncSoundSettingsUI();
  settingsModal.classList.remove("hidden");
  settingsModal.setAttribute("aria-hidden", "false");
}

function closeSettingsModal() {
  settingsModal.classList.add("hidden");
  settingsModal.setAttribute("aria-hidden", "true");
}

async function applySettings() {
  const payload = {
    work_duration: Number(workDurationInput.value),
    break_duration: Number(breakDurationInput.value),
    long_break_duration: Number(longBreakDurationInput.value),
    sessions_until_long_break: Number(sessionsUntilLongBreakInput.value),
  };
  await api("/api/config", { method: "POST", body: payload });
  state.workDuration = payload.work_duration || state.workDuration;
  state.breakDuration = payload.break_duration || state.breakDuration;
  state.longBreakDuration = payload.long_break_duration || state.longBreakDuration;
  state.sessionsUntilLongBreak = payload.sessions_until_long_break || state.sessionsUntilLongBreak;
  applyTheme(themeSelect.value);
  applySoundSettingsFromUI();
  closeSettingsModal();
  await refreshState();
  renderTimer();
}

async function refreshStats() {
  try {
    const [todayStats, weekStats, monthStats] = await Promise.all([
      api("/api/stats/today"),
      api("/api/stats/week"),
      api("/api/stats/month"),
    ]);
    const sessions = Number(todayStats.sessions || 0);
    const formatTime = todayStats.formatted_time || `${Math.floor((todayStats.total_focus_time || 0) / 60)}分`;

    sessionsValue.textContent = String(sessions);
    focusMinutesValue.textContent = formatTime;
    levelValue.textContent = `Lv.${todayStats.level || 1}`;
    streakValue.textContent = `${todayStats.streak_days || 0}日`;
    xpValue.textContent = `${todayStats.xp || 0} XP`;

    renderBadges(todayStats.badges || []);
    renderPeriodSummary(weekSummary, weekStats);
    renderPeriodSummary(monthSummary, monthStats);
    renderMiniChart(weekChart, weekStats.chart_data || [], 7);
    renderMiniChart(monthChart, monthStats.chart_data || [], 10);
  } catch (error) {
    setError(error.message);
  }
}

function renderBadges(badges) {
  badgeList.innerHTML = "";
  for (const badge of badges) {
    const chip = document.createElement("span");
    chip.className = `badge-chip${badge.achieved ? " achieved" : ""}`;
    chip.textContent = badge.achieved ? `🏅 ${badge.title}` : `🔒 ${badge.title}`;
    chip.setAttribute("aria-label", `${badge.title} - ${badge.achieved ? "達成済み" : "未達成"}`);
    badgeList.appendChild(chip);
  }
}

function renderPeriodSummary(target, periodStats) {
  const completionRate = Number(periodStats.completion_rate || 0).toFixed(1);
  const averageFocusMinutes = Math.floor((periodStats.average_focus_time || 0) / 60);
  target.textContent = `完了率: ${completionRate}% / 平均集中: ${averageFocusMinutes}分`;
}

function renderMiniChart(target, chartData, limit = 7) {
  target.innerHTML = "";
  const recentData = chartData.slice(-limit);
  target.style.gridTemplateColumns = `repeat(${Math.max(recentData.length, 1)}, 1fr)`;

  if (recentData.length === 0) {
    const placeholder = document.createElement("div");
    placeholder.className = "bar";
    placeholder.style.height = "4%";
    placeholder.style.opacity = "0.2";
    placeholder.title = "データなし";
    target.appendChild(placeholder);
    return;
  }

  const maxSessions = Math.max(1, ...recentData.map((item) => item.sessions || 0));

  for (const item of recentData) {
    const bar = document.createElement("div");
    bar.className = "bar";
    const sessions = item.sessions || 0;
    const height = Math.max(4, Math.round((sessions / maxSessions) * 100));
    bar.style.height = `${height}%`;
    bar.title = `${item.date}: ${sessions}回`;
    target.appendChild(bar);
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
      if (data.remaining > 0) {
        playNotificationSound("tick");
      }

      if (data.remaining === 0) {
        playNotificationSound("end");
        if (data.state === "working") {
          const breakState = await api("/api/timer/start-break", { method: "POST" });
          applyApiState(breakState);
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
    playNotificationSound("start");
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

darkModeBtn.addEventListener("click", () => {
  cycleTheme();
});

settingsBtn.addEventListener("click", () => {
  openSettingsModal();
});

closeSettingsBtn.addEventListener("click", () => {
  closeSettingsModal();
});

cancelSettingsBtn.addEventListener("click", () => {
  closeSettingsModal();
});

applySettingsBtn.addEventListener("click", () => {
  void applySettings();
});

settingsModal.addEventListener("click", (event) => {
  if (event.target === settingsModal) {
    closeSettingsModal();
  }
});

async function init() {
  applyTheme(state.theme);
  await loadConfig();
  await refreshState();
  if (state.mode === "working" || state.mode === "break") {
    startLoop();
  }
  await refreshStats();
}

void init();
