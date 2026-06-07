const form = document.getElementById("form");
const input = document.getElementById("input");
const messages = document.getElementById("messages");

// прокрутка вниз
function scrollDown() {
  messages.scrollTop = messages.scrollHeight;
}

// добавление сообщения
function addMessage(text, type) {
  const div = document.createElement("div");
  div.className = "msg " + type;

  div.innerHTML = marked.parse(text);

  messages.appendChild(div);
  scrollDown();

  // подсветка кода
  div.querySelectorAll("pre code").forEach((block) => {
    hljs.highlightElement(block);
  });
}

// отправка сообщения
async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = "";

  const botDiv = document.createElement("div");
  botDiv.className = "msg bot";
  botDiv.innerHTML = "⏳...";
  messages.appendChild(botDiv);
  scrollDown();

  try {
    const res = await fetch("https://new-1-5155.onrender.com/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    const data = await res.json();
    const answer = data.answer || "Ошибка ответа";

    botDiv.innerHTML = marked.parse(answer);

    botDiv.querySelectorAll("pre code").forEach((block) => {
      hljs.highlightElement(block);
    });

    scrollDown();

  } catch (e) {
    botDiv.innerHTML = "Ошибка соединения";
  }
}

// кнопка отправки формы
form.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage();
});

// 🔥 Enter / Shift+Enter (как в ChatGPT)
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault(); // не перенос строки
    sendMessage();      // отправка
  }
});
