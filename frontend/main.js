const form = document.getElementById('form');
const input = document.getElementById('input');
const messages = document.getElementById('messages');

const privateBtn = document.getElementById('privateBtn');
const clearBtn = document.getElementById('clearBtn');

const BACKEND = "https://new-1-5155.onrender.com/api/chat";

// 🧠 ID сессии
const SESSION_ID = "user-1";

/*
📦 состояние
*/
let chatHistory = [];
let isPrivate = false;

/*
💾 загрузка истории
*/
function loadHistory() {
messages.innerHTML = "";

const saved = localStorage.getItem('chat_history');

if (saved && !isPrivate) {
chatHistory = JSON.parse(saved);

```
chatHistory.forEach(m => {
  appendMessage(m.text, m.role);
});
```

}
}

/*
💾 сохранение истории
*/
function saveHistory() {
if (!isPrivate) {
localStorage.setItem('chat_history', JSON.stringify(chatHistory));
}
}

/*
💬 вывод сообщения
*/
function appendMessage(text, role = "bot") {
const el = document.createElement('div');

el.className = `msg ${role}`;
el.textContent = text;

messages.appendChild(el);
messages.scrollTop = messages.scrollHeight;

return el;
}

/*
🧠 добавить в историю
*/
function addToHistory(role, text) {
chatHistory.push({ role, text });
saveHistory();
}

/*
🚀 отправка сообщения
*/
form.addEventListener('submit', async (e) => {
e.preventDefault();

const text = input.value.trim();

if (!text) return;

appendMessage(text, 'user');
addToHistory('user', text);

input.value = '';

const thinkingMessage = appendMessage('✦ Думаю...', 'bot');

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

```
if (res.ok) {
  const data = await res.json();
  const reply = data.reply || '(пустой ответ)';

  thinkingMessage.textContent = reply;
  addToHistory('bot', reply);

} else {
  const errText = await res.text();
  const errorMsg = `Ошибка: ${res.status} ${errText}`;

  thinkingMessage.textContent = errorMsg;
  addToHistory('bot', errorMsg);
}
```

} catch (err) {
const errorMsg = `Сеть: ${err.message || err}`;

```
thinkingMessage.textContent = errorMsg;
addToHistory('bot', errorMsg);
```

}
});

/*
🗑 очистка
*/
clearBtn.addEventListener('click', () => {
chatHistory = [];
localStorage.removeItem('chat_history');
messages.innerHTML = '';
});

/*
🔒 приватный режим
*/
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

/*
🔄 старт
*/
loadHistory();
