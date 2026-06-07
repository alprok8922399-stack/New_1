const form = document.getElementById('form');
const input = document.getElementById('input');
const messages = document.getElementById('messages');

const privateBtn = document.getElementById('privateBtn');
const autoClearSelect = document.getElementById('autoClearSelect');

const BACKEND = "https://new-1-5155.onrender.com/api/chat";
const SESSION_ID = "user-1";

let chatHistory = [];
let isPrivate = false;

let autoClearTimer = null;

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

function clearChat() {
  chatHistory = [];
  localStorage.removeItem('chat_history');
  messages.innerHTML = '';
}

function resetAutoClearTimer() {

  if (!autoClearSelect) return;

  if (autoClearTimer) {
    clearTimeout(autoClearTimer);
  }

  const minutes = Number(autoClearSelect.value);

  if (minutes <= 0) return;

  autoClearTimer = setTimeout(() => {

    clearChat();

  }, minutes * 60 * 1000);
}

function enhanceCodeBlocks(container) {

  container.querySelectorAll("pre").forEach((pre) => {

    const code = pre.querySelector("code");

    if (code && window.hljs) {
      hljs.highlightElement(code);
    }

    if (pre.querySelector(".copy-btn")) return;

    pre.style.position = "relative";

    if (!code) return;

    const btn = document.createElement("button");

    btn.className = "copy-btn";
    btn.textContent = "Копировать";

    btn.style.position = "absolute";
    btn.style.top = "8px";
    btn.style.right = "8px";
    btn.style.background = "#444";
    btn.style.color = "#fff";
    btn.style.border = "none";
    btn.style.padding = "4px 8px";
    btn.style.borderRadius = "6px";
    btn.style.cursor = "pointer";
    btn.style.fontSize = "12px";

    btn.onclick = () => {

      navigator.clipboard.writeText(code.innerText);

      btn.textContent = "Скопировано";

      setTimeout(() => {
        btn.textContent = "Копировать";
      }, 1500);
    };

    pre.appendChild(btn);
  });
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

    enhanceCodeBlocks(el);

  } else {

    el.textContent = text;
  }

  messages.appendChild(el);

  setTimeout(scrollToBottom, 50);

  return el;
}

function saveHistory() {

  if (!isPrivate) {
    localStorage.setItem(
      'chat_history',
      JSON.stringify(chatHistory)
    );
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

  chatHistory.push({
    role,
    text
  });

  saveHistory();
}

form.addEventListener('submit', async (e) => {

  e.preventDefault();

  resetAutoClearTimer();

  const text = input.value.trim();

  if (!text) return;

  appendMessage(text, 'user');

  addToHistory('user', text);

  input.value = "";

  const thinking = appendMessage(
    '✦ Думаю...',
    'bot'
  );

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

      enhanceCodeBlocks(thinking);

      addToHistory(
        'bot',
        data.reply || '(пустой ответ)'
      );

      setTimeout(scrollToBottom, 50);

    } else {

      const err = await res.text();

      thinking.textContent =
        `Ошибка: ${res.status} ${err}`;
    }

  } catch (err) {

    thinking.textContent =
      `Сеть: ${err.message}`;
  }

  setTimeout(scrollToBottom, 50);
});

privateBtn.addEventListener('click', () => {

  isPrivate = !isPrivate;

  if (isPrivate) {

    privateBtn.textContent =
      "🔓 Приватный (ВКЛ)";

    messages.innerHTML = '';

  } else {

    privateBtn.textContent =
      "🔒 Приватный";

    loadHistory();
  }
});

if (autoClearSelect) {

  autoClearSelect.addEventListener(
    'change',
    resetAutoClearTimer
  );
}

loadHistory();

resetAutoClearTimer();
