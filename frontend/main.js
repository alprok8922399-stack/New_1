const form = document.getElementById("form");
const input = document.getElementById("input");
const messages = document.getElementById("messages");

const btnPrivate = document.getElementById("btnPrivate");
const clearTimer = document.getElementById("clearTimer");

let inactivityTimer = null;
let inactivityMinutes = 0;

function getSessionKey() {
  return localStorage.getItem("session_key") || "guest";
}

function scrollDown() {
  messages.scrollTop = messages.scrollHeight;
}

function autoResize() {
  input.style.height = "auto";
  input.style.height = input.scrollHeight + "px";
}

function clearChat() {
  messages.innerHTML = "";
}

function startTimer() {
  clearTimeout(inactivityTimer);

  if (!inactivityMinutes) return;

  inactivityTimer = setTimeout(() => {
    clearChat();
  }, inactivityMinutes * 60 * 1000);
}

function resetTimer() {
  if (inactivityMinutes > 0) {
    startTimer();
  }
}

function addMessage(text, type) {
  const div = document.createElement("div");

  div.className = "msg " + type;
  div.innerHTML = marked.parse(text);

  messages.appendChild(div);

  scrollDown();
  resetTimer();
}

function createBotMessage() {
  const div = document.createElement("div");

  div.className = "msg bot";
  div.innerHTML = "⏳...";

  messages.appendChild(div);

  scrollDown();

  return div;
}

async function sendMessage() {
  const text = input.value.trim();

  if (!text) return;

  addMessage(text, "user");

  input.value = "";
  input.style.height = "44px";

  const botDiv = createBotMessage();

  try {
    const res = await fetch("https://new-1-5155.onrender.com/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message: text,
        session_id: getSessionKey()
      })
    });

    const data = await res.json();

    botDiv.innerHTML = marked.parse(
      data.reply || "Ошибка ответа"
    );

    scrollDown();
    resetTimer();

  } catch (e) {
    botDiv.innerHTML = "Ошибка соединения";
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage();
});

input.addEventListener("input", () => {
  autoResize();
  resetTimer();
});

btnPrivate.addEventListener("click", () => {
  localStorage.setItem("mode", "private");

  clearChat();

  addMessage(
    "🔒 Приватный режим активирован",
    "bot"
  );
});

clearTimer.addEventListener("change", () => {

  if (clearTimer.value === "now") {
    clearChat();
    clearTimer.selectedIndex = 0;
    return;
  }

  inactivityMinutes = Number(clearTimer.value);

  clearTimeout(inactivityTimer);

  if (inactivityMinutes > 0) {
    startTimer();
  }
});

autoResize();
