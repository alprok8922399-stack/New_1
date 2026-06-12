const messagesDiv = document.getElementById("messages");
const form = document.getElementById("form");
const input = document.getElementById("input");

function addMessage(text, role) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.innerText = text;
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

form.onsubmit = async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  addMessage("Вы: " + text, "user");
  input.value = "";

  try {
    const res = await fetch("https://new-1-5155.onrender.com/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text, secret: "test-secret" })
    });

    if (!res.ok) {
      addMessage("Ошибка сети: " + res.status, "bot");
      return;
    }

    const data = await res.json();
    addMessage("Бот: " + data.text, "bot");
    
  } catch (err) {
    addMessage("Ошибка подключения: " + err.message, "bot");
  }
};
