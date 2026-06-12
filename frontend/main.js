const messagesDiv = document.getElementById("messages");
const form = document.getElementById("form");
const input = document.getElementById("input");
const autoClearSelect = document.getElementById("autoClearSelect");
const privateBtn = document.getElementById("privateBtn");

// Загрузка истории при старте
async function loadHistory() {
  const res = await fetch("https://new-1-5155.onrender.com/api/history");
  const data = await res.json();
  data.forEach(msg => addMessage(msg.content, msg.role));
}

function addMessage(text, role) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.innerHTML = marked.parse(text);
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  div.querySelectorAll("pre code").forEach(hljs.highlightElement);
}

form.onsubmit = async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = "";

  const res = await fetch("https://new-1-5155.onrender.com/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: text })
  });

  const data = await res.json();
  addMessage(data.text, "assistant");
};

// Таймер очистки (базовая логика)
autoClearSelect.onchange = () => {
  const minutes = parseInt(autoClearSelect.value);
  if (minutes > 0) {
    setTimeout(() => {
      messagesDiv.innerHTML = "";
    }, minutes * 60000);
  }
};

loadHistory();
