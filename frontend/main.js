const form = document.getElementById("form");
const input = document.getElementById("input");
const messages = document.getElementById("messages");

// 🔥 плавный скролл
function scrollDown(smooth = true) {
  messages.scrollTo({
    top: messages.scrollHeight,
    behavior: smooth ? "smooth" : "auto"
  });
}

// авто-рост textarea
function autoResize() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 120) + "px";
}

// добавление сообщения пользователя
function addUserMessage(text) {
  const div = document.createElement("div");
  div.className = "msg user";
  div.innerHTML = marked.parse(text);
  messages.appendChild(div);
  scrollDown(false);
}

// создание пустого сообщения бота
function createBotMessage() {
  const div = document.createElement("div");
  div.className = "msg bot";
  div.innerHTML = "";
  messages.appendChild(div);
  scrollDown(false);
  return div;
}

// эффект печати
function typeText(element, text, speed = 10) {
  let i = 0;
  element.innerHTML = "";

  const interval = setInterval(() => {
    element.innerHTML += text[i];
    i++;

    scrollDown(false);

    if (i >= text.length) {
      clearInterval(interval);

      // после печати применяем markdown
      const html = marked.parse(text);
      element.innerHTML = html;

      element.querySelectorAll("pre code").forEach((block) => {
        hljs.highlightElement(block);
      });

      scrollDown(true);
    }
  }, speed);
}

// отправка сообщения
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
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    const data = await res.json();
    const answer = data.answer || "Ошибка ответа";

    // 🔥 печать как живой AI
    typeText(botDiv, answer);

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
