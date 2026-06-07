const form = document.getElementById("form");
const input = document.getElementById("input");
const messages = document.getElementById("messages");

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

    // 🔥 ВАЖНОЕ ИСПРАВЛЕНИЕ
    const answer = data.reply || "Ошибка ответа";

    botDiv.innerHTML = marked.parse(answer);

    botDiv.querySelectorAll("pre code").forEach((block) => {
      hljs.highlightElement(block);
    });

    scrollDown(true);

  } catch (e) {
    botDiv.innerHTML = "Ошибка соединения";
  }
}

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
