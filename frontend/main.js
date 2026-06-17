const messagesContainer = document.getElementById('messages');
const inputArea = document.getElementById('input');
const sendBtn = document.getElementById('send-btn');

// Авто-рост поля ввода
inputArea.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

function appendMessage(text, isUser) {
    const div = document.createElement('div');
    div.className = isUser ? 'message user' : 'message bot';
    // Простая обработка абзацев
    div.innerHTML = text.replace(/\n/g, '<br>');
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

sendBtn.addEventListener('click', async () => {
    const text = inputArea.value.trim();
    if (!text) return;
    
    appendMessage(text, true); // Добавляем сразу!
    inputArea.value = '';
    inputArea.style.height = '40px';

    try {
        const response = await fetch("https://new-1-5155.onrender.com/api/chat", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        const data = await response.json();
        appendMessage(data.text, false); // Ответ бота
    } catch (e) {
        appendMessage("Ошибка соединения", false);
    }
});
