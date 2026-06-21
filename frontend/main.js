const messagesContainer = document.getElementById('messages');
const inputArea = document.getElementById('input');
const sendBtn = document.getElementById('send-btn');

// Нам нужно знать, кто пишет
let currentUser = "Гость";

// Обновим функцию отправки, чтобы она передавала имя
sendBtn.addEventListener('click', async () => {
    const text = inputArea.value.trim();
    if (!text) return;
    
    appendMessage(text, true);
    inputArea.value = '';
    inputArea.style.height = '40px';

    try {
        const response = await fetch("https://new-1-5155.onrender.com/api/chat", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // Передаем имя пользователя вместе с сообщением
            body: JSON.stringify({ text: text, user: currentUser })
        });
        const data = await response.json();
        appendMessage(data.text, false);
    } catch (e) {
        appendMessage("Ошибка соединения.", false);
    }
});

// Обновим функцию загрузки истории
async function loadChatHistory(name = "Гость") {
    currentUser = name;
    try {
        const response = await fetch(`https://new-1-5155.onrender.com/api/history?user=${encodeURIComponent(name)}`);
        const history = await response.json();
        messagesContainer.innerHTML = ""; 
        history.forEach(msg => {
            const isUser = msg.role === 'user';
            appendMessage(msg.content || msg.text, isUser);
        });
    } catch (e) {
        console.error("Ошибка загрузки:", e);
    }
}

// Форматирование текста (оставляем как было)
function formatAiText(text) {
    let rawText = text || "";
    rawText = rawText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    rawText = rawText.replace(/\*(.*?)\*/g, '<em>$1</em>');
    rawText = rawText.replace(/\*/g, '');
    const paragraphs = rawText.split('\n');
    return paragraphs.map(p => p.trim() === "" ? '<div style="height: 10px;"></div>' : `<p style="margin-bottom: 8px; line-height: 1.5;">${p}</p>`).join('');
}

function appendMessage(text, isUser) {
    const messageElement = document.createElement('div');
    messageElement.className = isUser ? 'message user' : 'message bot';
    messageElement.innerHTML = `<div class="message-text">${isUser ? text.replace(/\n/g, '<br>') : formatAiText(text)}</div>`;
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
