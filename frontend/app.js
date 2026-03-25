/**
 * app.js – ContextDesk Chat UI
 *
 * Connects to the FastAPI backend at /api/v1/chat.
 * Manages session_id, message rendering, typing indicator.
 */

const API_BASE = "http://localhost:8000/api/v1";

// ---- State ----
let sessionId = crypto.randomUUID();

// ---- DOM Refs ----
const messagesEl = document.getElementById("messages");
const chatForm   = document.getElementById("chat-form");
const inputEl    = document.getElementById("user-input");
const btnSend    = document.getElementById("btn-send");
const btnClear   = document.getElementById("btn-clear");

// ---- Init ----
inputEl.focus();

// ---- Events ----
chatForm.addEventListener("submit", onSubmit);
btnClear.addEventListener("click", clearConversation);

async function onSubmit(e) {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;

  disable(true);
  appendUserMessage(text);
  inputEl.value = "";

  const typingId = appendTypingIndicator();

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message: text }),
    });

    removeTypingIndicator(typingId);

    if (!res.ok) {
      appendBotMessage("Lo siento, ha ocurrido un error al contactar con el servidor.", false);
      return;
    }

    // --- Streaming Handle ---
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let botMessageText = "";
    let isFirstChunk = true;
    let statusEl = null;

    // Create an empty bot message element that we'll update
    const botMsgEl = createBotMessageElement("", false);
    const bodyEl = botMsgEl.querySelector(".message-body");
    messagesEl.appendChild(botMsgEl);

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });

      if (isFirstChunk) {
        // First chunk is always the UX placeholder from StreamingGuard (ends with \n\n)
        // Render it as an italic status line, not as the real response
        if (chunk.endsWith("\n\n")) {
          statusEl = document.createElement("div");
          statusEl.className = "message-status";
          statusEl.innerHTML = `
            <div class="typing-dots">
              <span></span><span></span><span></span>
            </div>
            <span>${chunk.trim()}</span>
          `;
          bodyEl.appendChild(statusEl);
          scrollToBottom();
          isFirstChunk = false;
          continue; // wait for real content
        }
        isFirstChunk = false;
      }

      // Real content is flowing — remove the status placeholder if it exists
      if (statusEl) {
        statusEl.remove();
        statusEl = null;
      }

      botMessageText += chunk;
      bodyEl.innerHTML = formatText(botMessageText);
      scrollToBottom();
    }

  } catch (err) {
    removeTypingIndicator(typingId);
    console.error("Fetch error:", err);
    appendBotMessage(
      "No se pudo conectar con el asistente. Comprueba que el servidor está activo en <code>localhost:8000</code>.",
      false
    );
  } finally {
    disable(false);
    inputEl.focus();
  }
}

function clearConversation() {
  sessionId = crypto.randomUUID();
  // Remove all messages except welcome
  const msgs = messagesEl.querySelectorAll(".message:not(#msg-welcome)");
  msgs.forEach(m => m.remove());
  inputEl.focus();
}

// ---- Message Rendering ----
function appendUserMessage(text) {
  const el = document.createElement("div");
  el.className = "message message--user";
  el.innerHTML = `
    <div class="message-avatar" aria-hidden="true">👤</div>
    <div class="message-body">${escapeHtml(text)}</div>
  `;
  messagesEl.appendChild(el);
  scrollToBottom();
}

function appendBotMessage(text, isBlocked) {
  const el = createBotMessageElement(text, isBlocked);
  messagesEl.appendChild(el);
  scrollToBottom();
}

function createBotMessageElement(text, isBlocked) {
  const el = document.createElement("div");
  el.className = "message message--bot" + (isBlocked ? " message--blocked" : "");

  const blockedLabel = isBlocked
    ? `<div class="blocked-label"><span>⚠️</span> Consulta no permitida</div>`
    : "";

  el.innerHTML = `
    <div class="message-avatar" aria-hidden="true">
      <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="32" height="32" rx="10" fill="url(#avg2)"/>
        <path d="M16 8v16M8 16h16" stroke="white" stroke-width="3" stroke-linecap="round"/>
        <defs>
          <linearGradient id="avg2" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop stop-color="${isBlocked ? '#ef4444' : '#0ea5e9'}"/>
            <stop offset="1" stop-color="${isBlocked ? '#f97316' : '#14b8a6'}"/>
          </linearGradient>
        </defs>
      </svg>
    </div>
    <div class="message-body">
      ${blockedLabel}
      ${formatText(text)}
    </div>
  `;
  return el;
}

function appendTypingIndicator() {
  const id = `typing-${Date.now()}`;
  const el = document.createElement("div");
  el.id = id;
  el.className = "message message--bot message--typing";
  el.setAttribute("aria-label", "El asistente está escribiendo");
  el.innerHTML = `
    <div class="message-avatar" aria-hidden="true">
      <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="32" height="32" rx="10" fill="url(#avt)"/>
        <path d="M16 8v16M8 16h16" stroke="white" stroke-width="3" stroke-linecap="round"/>
        <defs>
          <linearGradient id="avt" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop stop-color="#0ea5e9"/><stop offset="1" stop-color="#14b8a6"/>
          </linearGradient>
        </defs>
      </svg>
    </div>
    <div class="message-body">
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
  messagesEl.appendChild(el);
  scrollToBottom();
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ---- Helpers ----
function disable(state) {
  inputEl.disabled = state;
  btnSend.disabled = state;
}

function scrollToBottom() {
  messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: "smooth" });
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatText(text) {
  // Basic markdown-lite: bold, line breaks
  return escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br/>");
}
