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
  div.innerHTML = "⏳ отправка...";
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

    console.log("STATUS:", res.status);

    const raw = await res.text();
    console.log("RAW RESPONSE:", raw);

    let data;
    try {
      data = JSON.parse(raw);
    } catch (e) {
      botDiv.innerHTML = "Ошибка: сервер вернул не JSON";
      return;
    }

    if (!data.reply) {
      botDiv.innerHTML = "Ошибка: нет reply в ответе";
      console.log(data);
      return;
    }

    botDiv.innerHTML = marked.parse(data.reply);
    scrollDown();

  } catch (e) {
    console.log("FETCH ERROR:", e);
    botDiv.innerHTML = "Ошибка соединения с сервером";
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage();
});
