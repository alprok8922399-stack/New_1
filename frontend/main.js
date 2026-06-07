const form = document.getElementById('form');
const input = document.getElementById('input');
const messages = document.getElementById('messages');

const privateBtn = document.getElementById('privateBtn');
const clearBtn = document.getElementById('clearBtn');

const BACKEND = "https://new-1-5155.onrender.com/api/chat";
const SESSION_ID = "user-1";

let chatHistory = [];
let isPrivate = false;

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

function renderMarkdown(text) {
  if (window.marked) {
    return marked.parse(text || "");
  }

  return text || "";
}

function appendMessage(text, role = "bot") {
  const el = document.createElement('div');
  el.className = `msg ${role}`;

  if (role === "bot") {
    el.innerHTML = renderMarkdown(text);
  } else {
    el.textContent = text;
  }

  messages.appendChild(el);

  setTimeout(scrollToBottom, 50);

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

    chatHistory.forEach(m => {
      appendMessage(m.text, m.role);
    });
  }

  setTimeout(scrollToBottom, 50);
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

    if (res.ok) {
      const data = await res.json();

      thinking.innerHTML = renderMarkdown(
        data.reply || '(пустой ответ)'
      );

      addToHistory(
        'bot',
        data.reply || '(пустой ответ)'
      );

      setTimeout(scrollToBottom, 50);

    } else {
      const err = await res.text();
      thinking.textContent = `Ошибка: ${res.status} ${err}`;
    }

  } catch (err) {
    thinking.textContent = `Сеть: ${err.message}`;
  }

  setTimeout(scrollToBottom, 50);
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
