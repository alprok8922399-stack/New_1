const messagesContainer = document.getElementById('messages');
const inputArea = document.getElementById('input');
const sendBtn = document.getElementById('send-btn');

// Функция добавления сообщений (теперь надежная)
function appendMessage(text, isUser) {
    const className = isUser ? 'message user' : 'message bot';
    // Используем insertAdjacentHTML, чтобы не трогать старые сообщения
    messagesContainer.insertAdjacentHTML('beforeend', `<div class="${className}">${text.replace(/\n/g, '<br>')}</div>`);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Загрузка истории
async function loadChatHistory() {
    try {
        const response = await fetch("https://new-1-5155.onrender.com/api/history");
        const history = await response.json();
        // Очищаем только при первой загрузке!
        messagesContainer.innerHTML = ""; 
        history.forEach(msg => appendMessage(msg.content, msg.role === 'user'));
    } catch (e) {
        console.error("Ошибка загрузки истории:", e);
    }
}

sendBtn.addEventListener('click', async () => {
    const text = inputArea.value.trim();
    if (!text) return;
    
    appendMessage(text, true); // Добавляем сообщение пользователя
    inputArea.value = '';
    inputArea.style.height = '40px';

    try {
        const response = await fetch("https://new-1-5155.onrender.com/api/chat", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        const data = await response.json();
        appendMessage(data.text, false); // Добавляем ответ бота
    } catch (e) {
        appendMessage("Ошибка соединения.", false);
    }
});

// Запуск при открытии
document.addEventListener('DOMContentLoaded', loadChatHistory);
