const form = document.getElementById("form");
const input = document.getElementById("input");
const messages = document.getElementById("messages");

function getSessionKey() {
  return localStorage.getItem("session_key") || "guest";
}

function scrollDown() {
  messages.scrollTop = messages.scrollHeight;
}

function addMessage(text, type) {
  const div = document.createElement("div");
  div.className = "msg " + type;
  div.innerHTML = marked.parse(text);
  messages.appendChild(div);
  scrollDown();
}

function createBotMessage() {
  const div = document.createElement("div");
  div.className = "msg bot";
  div.innerHTML = "⏳";
  messages.appendChild(div);
  scrollDown();
  return div;
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = "";

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

    const reply = data.reply;

    if (!reply) {
      botDiv.innerHTML = "Ошибка ответа (пустой ответ)";
      return;
    }

    botDiv.innerHTML = marked.parse(reply);
    scrollDown();

  } catch (e) {
    botDiv.innerHTML = "Ошибка соединения с сервером";
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage();
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    sendMessage();
  }
});
