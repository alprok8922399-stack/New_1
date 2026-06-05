const form = document.getElementById('form');
const input = document.getElementById('input');
const messages = document.getElementById('messages');

const BACKEND = "https://new-1-5155.onrender.com/api/chat";

function appendMessage(text, cls = "bot") {
  const el = document.createElement('div');
  el.className = `msg ${cls}`;
  el.textContent = text;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const text = input.value.trim();
  if (!text) return;

  appendMessage(text, 'user');
  input.value = '';

  appendMessage('...', 'bot');

  try {
    const res = await fetch(BACKEND, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: text
      })
    });

    const last = messages.querySelectorAll('.msg.bot');

    if (res.ok) {
      const data = await res.json();
      last[last.length - 1].textContent =
        data.reply || '(пустой ответ)';
    } else {
      const err = await res.text();
      last[last.length - 1].textContent =
        `Ошибка: ${res.status} ${err}`;
    }
  } catch (err) {
    const last = messages.querySelectorAll('.msg.bot');
    last[last.length - 1].textContent =
      `Сеть: ${err.message || err}`;
  }
});
