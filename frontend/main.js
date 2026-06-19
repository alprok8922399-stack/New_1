const messagesContainer = document.getElementById('messages');
const inputArea = document.getElementById('input');
const sendBtn = document.getElementById('send-btn');

// Функция для получения текущей даты и времени в формате «ДД.ММ.ГГГГ, ЧЧ:ММ»
function getFormattedDate() {
  const now = new Date();
  const day = String(now.getDate()).padStart(2, '0');
  const month = String(now.getMonth() + 1).padStart(2, '0'); // Месяц начинается с 0
  const year = now.getFullYear();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  return `${day}.${month}.${year}, ${hours}:${minutes}`;
}

// Автоматическое расширение поля ввода при написании текста
inputArea.addEventListener('input', function() {
  this.style.height = 'auto';
  this.style.height = (this.scrollHeight) + 'px';
});

// Функция, которая делает текст ИИ красивым (как у Gemini)
function formatAiText(text) {
  let rawText = text || "";

  // 1. Превращаем двойные звёздочки **текст** в жирный шрифт
  rawText = rawText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // 2. Превращаем одиночные звёздочки *текст* в красивый курсив
  rawText = rawText.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // 3. Вычищаем сиротливые одиночные звёздочки, если остались
  rawText = rawText.replace(/\*/g, '');

  // 4. Разбиваем текст на абзацы по переносам строк
  const paragraphs = rawText.split('\n');

  // Заворачиваем каждую строчку в абзац с отступом снизу
  let formattedHtml = paragraphs.map(p => {
    if (p.trim() === '---' || p.trim() === '***') {
      return '<hr style="border: 0; border-top: 1px solid #333; margin: 12px 0;">';
    }
    if (p.trim() === "") {
      return '<div style="height: 10px;"></div>'; // Пустая строка для отступа
    }
    return `<p style="margin-bottom: 8px; line-height: 1.5;">${p}</p>`;
  }).join('');

  return formattedHtml;
}

// Функция для копирования текста в буфер обмена
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    alert('Текст скопирован!');
  }).catch(err => {
    console.error('Не удалось скопировать: ', err);
  });
}

// Функция добавления сообщений в ленту
function appendMessage(text, isUser) {
  const className = isUser ? 'message user' : 'message bot';

  // Получаем текущую дату и время
  const messageDate = getFormattedDate();

  // Форматируем текст: добавляем дату в начале
  const finalHtml = isUser
    ? `${messageDate}<br>${text.replace(/\n/g, '<br>')}`
    : `${messageDate}<br>${formatAiText(text)}`;

  // Генерируем кнопки в зависимости от того, кто отправил сообщение
  let buttonsHtml = '';
  if (isUser) {
    buttonsHtml = `
      <div class="message-buttons" style="text-align: right; margin-top: 4px;">
        <button class="btn-edit" style="background: none; border: none; color: #888; cursor: pointer; font-size: 12px; margin-right: 8px;">✏️ Редактировать</button>
        <button class="btn-copy" style="background: none; border: none; color: #888; cursor: pointer; font-size: 12px;">📋 Скопировать</button>
      </div>
    `;
  } else {
    buttonsHtml = `
      <div class="message-buttons" style="text-align: left; margin-top: 4px;">
        <button class="btn-copy" style="background: none; border: none; color: #888; cursor: pointer; font-size: 12px;">📋 Скопировать</button>
      </div>
    `;
  }

  // Создаём элемент сообщения
  const messageElement = document.createElement('div');
  messageElement.className = className;
  messageElement.innerHTML = `
    <div class="message-text">${finalHtml}</div>
    ${buttonsHtml}
  `;

  // Навешиваем событие на кнопку копирования
  const copyBtn = messageElement.querySelector('.btn-copy');
  if (copyBtn) {
    copyBtn.addEventListener('click', () => copyToClipboard(text));
  }

  // Навешиваем событие на кнопку редактирования
  const editBtn = messageElement.querySelector('.btn-edit');
  if (editBtn) {
    editBtn.addEventListener('click', () => {
      inputArea.value = text;
      inputArea.focus();
      inputArea.style.height = 'auto';
      inputArea.style.height = (inputArea.scrollHeight) + 'px';
    });
  }

  messagesContainer.appendChild(messageElement);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Загрузка истории чата из базы данных
async function loadChatHistory() {
  try {
    const response = await fetch("https://new-1-5155.onrender.com/api/history");
    const history = await response.json();
    messagesContainer.innerHTML = "";
    history.forEach(msg => {
      const isUser = msg.role === 'user';
      appendMessage(msg.content || msg.text, isUser);
    });
  } catch (e) {
    console.error("Ошибка загрузки истории:", e);
  }
}

// Нажатие на кнопку отправки
sendBtn.addEventListener('click', async () => {
  const text = inputArea.value.trim();
  if (!text) return;

  appendMessage(text, true); // Сразу выводим сообщение пользователя
  inputArea.value = '';
  inputArea.style.height = '40px'; // Возвращаем исходный размер полю ввода

  try {
    const response = await fetch("https://new-1-5155.onrender.com/api/chat", {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    });
    const data = await response.json();
    appendMessage(data.text, false); // Выводим красивый ответ бота
  } catch (e) {
    appendMessage("Ошибка соединения. Кажется, сервер спит.", false);
  }
});

// Запуск истории при открытии страницы
document.addEventListener('DOMContentLoaded', loadChatHistory);
  
