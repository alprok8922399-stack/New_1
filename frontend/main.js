const form = document.getElementById("form");
const input = document.getElementById("input");
const messages = document.getElementById("messages");

/* =========================
   КЛЮЧ ПОЛЬЗОВАТЕЛЯ
========================= */

function getUserKey() {
  return localStorage.getItem("user_key") || null;
}

function setUserKey(key) {
  localStorage.setItem("user_key", key);
}

/* =========================
   ПЕРВЫЙ ВХОД — ВОПРОС
========================= */

function askForKey() {
  let key = getUserKey();

  if (!key) {
    key = prompt("Как твоё имя?");
    
    if (!key) {
      key = "guest";
    }

    setUserKey(key);
  }
}

askForKey();

/* =========================
   UI
========================= */

function scrollDown(smooth = true) {
  messages.scrollTo({
    top: messages.scrollHeight,
    behavior: smooth ? "smooth" : "auto"
  });
}

function autoResize() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 120) + "px";
}

function addUserMessage(text) {
  const div = document.createElement("div");
  div.className = "msg user";
  div.innerHTML = marked.parse(text);
  messages.appendChild(div);
  scrollDown(false);
}

function createBotMessage() {
  const div = document.createElement("div");
  div.className = "msg bot";
  div.innerHTML = "⏳...";
  messages.appendChild(div);
  scrollDown(false);
  return div;
}

/* =========================
   КНОПКА COPY
========================= */

function addCopyButtons(container) {
  container.querySelectorAll("pre").forEach((pre) => {
    if (pre.querySelector(".copy-btn")) return;

    const btn = document.createElement("button");
    btn.innerText = "Copy";
    btn.className = "copy-btn";

    btn.onclick = () => {
      const code = pre.querySelector("code");
      if (!code) return;

      navigator.clipboard.writeText(code.innerText);

      btn.innerText = "Copied!";
      setTimeout(() => (btn.innerText = "Copy"), 1500);
    };

    pre.style.position = "relative";
    pre.appendChild(btn);
  });
}

/* =========================
   РЕНДЕР БОТА
========================= */

function renderBotMessage(div, text) {
  div.innerHTML = marked.parse(text);

  div.querySelectorAll("pre code").forEach((block) => {
    hljs.highlightElement(block);
  });

  addCopyButtons(div);
  scrollDown(true);
}

/* =========================
   ОТПРАВКА
========================= */

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  addUserMessage(text);
  input.value = "";
  autoResize();

  const botDiv = createBotMessage();

  try {
    const res = await fetch("https://new-1-5155.onrender.com/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message: text,
        session_id: getUserKey()
      })
    });

    const data = await res.json();
    const answer = data.reply || "Ошибка ответа";

    renderBotMessage(botDiv, answer);

  } catch (e) {
    botDiv.innerHTML = "Ошибка соединения";
  }
}

/* =========================
   EVENTS
========================= */

form.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage();
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

input.addEventListener("input", autoResize);
