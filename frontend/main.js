const form = document.getElementById("form");
const input = document.getElementById("input");
const messages = document.getElementById("messages");

// 🔥 плавный скролл вниз
function scrollDown(smooth = true) {
  messages.scrollTo({
    top: messages.scrollHeight,
    behavior: smooth ? "smooth" : "auto"
  });
}

// авто-увеличение textarea
function autoResize() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 120) + "px";
}

// добавление сообщения
function addMessage(text, type) {
  const div = document.createElement("div");
  div.className = "msg " + type;

  div.innerHTML = marked.parse(text);

  messages.appendChild(div);
  scrollDown(false);

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
  autoResize();

  const botDiv = document.createElement("div");
  botDiv.className = "msg bot";
  botDiv.innerHTML = "⏳...";
  messages.appendChild(botDiv);

  scrollDown(false);

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

    scrollDown(true);

  } catch (e) {
    botDiv.innerHTML = "Ошибка соединения";
  }
}

// отправка формы
form.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage();
});

// Enter / Shift+Enter
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// авто-рост поля
input.addEventListener("input", autoResize);
