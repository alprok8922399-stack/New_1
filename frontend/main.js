const messagesContainer = document.getElementById('messages');
const inputArea = document.getElementById('input');
const sendBtn = document.getElementById('send-btn');


function getFormattedDate() {
  const now = new Date();
  const day = String(now.getDate()).padStart(2, '0');
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const year = now.getFullYear();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  return `${day}.${month}.${year}, ${hours}:${minutes}`;
}

function appendMessage(text, isUser) {
  const messageElement = document.createElement('div');
  messageElement.className = isUser ? 'message user' : 'message bot';
  const date = getFormattedDate();
  messageElement.innerHTML = `<div><strong>${date}</strong><br>${text}</div>`;
  messagesContainer.appendChild(messageElement);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

sendBtn.addEventListener('click', () => {
  const text = inputArea.value.trim();
  if (!text) return;

  // ЖЁСТКИЙ ПЕРЕХВАТ запросов про дату/время
  const lowerText = text.toLowerCase();
  if (
    lowerText.includes('дата') ||
    lowerText.includes('время') ||
    lowerText.includes('который час') ||
    lowerText.includes('сейчас') ||
    lowerText.includes('какое число') ||
    lowerText.includes('сегодняшняя дата')
  ) {
    appendMessage(`Текущая дата и время: ${getFormattedDate()}`, false);
    inputArea.value = '';
    return; // Прерываем выполнение — не идём к fetch
  }

  // Если не запрос про дату — показываем сообщение пользователя
  appendMessage(text, true);
  inputArea.value = '';
});

document.addEventListener('DOMContentLoaded', () => {
  messagesContainer.innerHTML = '';
});
