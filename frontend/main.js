const form = document.getElementById('form');
const input = document.getElementById('input');
const messages = document.getElementById('messages');

const privateBtn = document.getElementById('privateBtn');
const clearBtn = document.getElementById('clearBtn');

const BACKEND = "https://new-1-5155.onrender.com/api/chat";
const SESSION_ID = "user-1";

let chatHistory = [];
let isPrivate = false;

function appendMessage(text, role = "bot") {
  const el = document.createElement('div');
  el.className = `msg ${role}`;
  el.textContent = text;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
  return el;
}

function saveHistory() {
  if (!isPrivate) {
    localStorage.setItem('chat_history', JSON.stringify(chatHistory));
  }
}

function loadHistory() {
  messages.innerHTML = "";

  const saved = localStorage.getItem('chat_history');

  if (saved && !isPrivate) {
    chatHistory = JSON.parse(saved);
    chatHistory.forEach(m => appendMessage(m.text, m.role));
  }
}

function addToHistory(role, text) {
  chatHistory.push({ role, text });
  saveHistory();
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const text = input.value.trim();

  if (!text) return;

  appendMessage(text, 'user');
  addToHistory('user', text);

  input.value = "";

  const thinking = appendMessage('✦ Думаю...', 'bot');

  try {
    const res = await fetch(BACKEND, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: text,
        session_id: SESSION_ID
      })
    });

    const raw = await res.text();

    console.log("STATUS:", res.status);
    console.log("RAW:", raw);

    if (!res.ok) {
      thinking.textContent = `Ошибка ${res.status}: ${raw}`;
      return;
    }

    let data;

    try {
      data = JSON.parse(raw);
    } catch {
      thinking.textContent = `Некорректный JSON: ${raw}`;
      return;
    }

    thinking.textContent = data.reply || "(пустой ответ)";
    addToHistory('bot', thinking.textContent);

  } catch (err) {
    thinking.textContent = `Сеть: ${err.message}`;
  }
});

clearBtn.addEventListener('click', () => {
  chatHistory = [];
  localStorage.removeItem('chat_history');
  messages.innerHTML = '';
});

privateBtn.addEventListener('click', () => {
  isPrivate = !isPrivate;

  if (isPrivate) {
    privateBtn.textContent = "🔓 Приватный (ВКЛ)";
    messages.innerHTML = '';
  } else {
    privateBtn.textContent = "🔒 Приватный";
    loadHistory();
  }
});

loadHistory();
