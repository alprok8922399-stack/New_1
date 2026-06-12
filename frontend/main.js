const messagesDiv = document.getElementById("messages");
const form = document.getElementById("form");
const input = document.getElementById("input");

// ВРЕМЕННО: используем ключ, чтобы бэкенд нас пустил
const MY_SECRET = "test-secret"; 

function addMessage(text, role) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.innerText = text; // Убрали marked пока что для теста
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

form.onsubmit = async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = "";

  try {
    const res = await fetch("https://new-1-5155.onrender.com/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text, secret: MY_SECRET })
    });

    const data = await res.json();
    addMessage(data.text || "Ошибка: сервер не ответил", "bot");
  } catch (err) {
    addMessage("Ошибка сети", "bot");
  }
};
