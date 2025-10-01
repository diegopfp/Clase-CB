// Selección de elementos
const $ = (id) => document.getElementById(id);
const chat = $("cde-chat");
const launcher = $("cde-launcher");
const closeBtn = $("cde-close");
const msgs = $("cde-msgs");
const promptEl = $("cde-prompt");
const form = $("cde-form");
const apiInput = $("cde-api");
const healthBtn = $("cde-check");
const healthBadge = $("cde-health");

function addMsg(text, who = "ai") {
  const div = document.createElement("div");
  div.className = "msg " + (who === "me" ? "me" : "ai");
  div.textContent = text;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

async function checkHealth() {
  setPill("warn", "Comprobando…");
  const base = apiInput.value.trim();
  try {
    const r = await fetch(`${base}/health`, { method: "GET" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const j = await r.json();
    setPill("ok", j.model ? `API OK · ${j.model}` : "API OK");
  } catch (e) {
    setPill("err", "API fuera");
  }
}

function setPill(kind, text) {
  healthBadge.className = "pill " + (kind === "ok" ? "pill-ok" : kind === "err" ? "pill-err" : "pill-warn");
  healthBadge.textContent = text;
}

async function sendPrompt(promptText) {
  const base = apiInput.value.trim();
  try {
    const r = await fetch(`${base}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: promptText })
    });
    if (!r.ok) {
      const err = await r.text();
      throw new Error(err || `HTTP ${r.status}`);
    }
    const j = await r.json();
    return j.output || "(sin salida)";
  } catch (e) {
    return `Error: ${e.message || e}`;
  }
}

// Abrir / cerrar
launcher.addEventListener("click", () => {
  chat.hidden = false;
  // primer health al abrir
  if (healthBadge.textContent.includes("Comprobando") || healthBadge.textContent === "")
    checkHealth();
  // focus
  setTimeout(() => promptEl.focus(), 100);
});
closeBtn.addEventListener("click", () => { chat.hidden = true; });

// Health manual
healthBtn.addEventListener("click", checkHealth);

// Auto-expand del textarea
promptEl.addEventListener("input", () => {
  promptEl.style.height = "auto";
  promptEl.style.height = Math.min(promptEl.scrollHeight, 120) + "px";
});

// Enviar
form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const text = (promptEl.value || "").trim();
  if (!text) return;

  addMsg(text, "me");
  promptEl.value = "";
  promptEl.style.height = "42px";

  const reply = await sendPrompt(text);
  addMsg(reply, "ai");
});

// Intento de Enter=Enviar, Shift+Enter nueva línea
promptEl.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter" && !ev.shiftKey) {
    ev.preventDefault();
    form.dispatchEvent(new Event("submit", { cancelable: true }));
  }
});

// Chequeo inicial (por si la UI se abre ya visible)
if (!chat.hidden) checkHealth();
