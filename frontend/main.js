const messagesContainer = document.getElementById('messages');
const inputArea = document.getElementById('input');
const sendBtn = document.getElementById('send-btn');

const style = document.createElement('style');
style.innerHTML = `
    .hourglass { display: inline-block; width: 20px; height: 20px; border: 2px solid #888; border-radius: 4px; position: relative; animation: rotate 2s linear infinite; }
    .hourglass::before { content: ''; position: absolute; top: 2px; left: 2px; right: 2px; bottom: 2px; border: 1px solid #888; clip-path: polygon(0 0, 100% 0, 50% 50%, 100% 100%, 0 100%, 50% 50%); }
    @keyframes rotate { 100% { transform: rotate(180deg); } }
`;
document.head.appendChild(style);

if (inputArea) {
    inputArea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
}

function formatAiText(text) {
    let rawText = text || "";
    const codeBlockPattern = new RegExp('\\`\\`\\`(?:[a-zA-Z0-9_-]+)?\\n([\\s\\S]*?)\\`\\`\\`', 'g');
    rawText = rawText.replace(codeBlockPattern, (match, codeContent) => {
        const cleanCode = codeContent.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").trim();
        return `<div style="background-color: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 14px; white-space: pre-wrap; margin: 10px 0; border: 1px solid #333;">${cleanCode}</div>`;
    });
    rawText = rawText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    rawText = rawText.replace(/\*(.*?)\*/g, '<em>$1</em>');
    rawText = rawText.replace(/\*/g, '');
    return rawText.split('\n').map(p => {
        if (p.trim() === '---') return '<hr style="border: 0; border-top: 1px solid #333;">';
        if (p.trim() === "") return '<div style="height: 10px;"></div>';
        if (p.includes('background-color:')) return p;
        return `<p style="margin-bottom: 8px;">${p}</p>`;
    }).join('');
}

function appendMessage(text, isUser, isLoader = false) {
    const className = isUser ? 'message user' : 'message bot';
    const content = isLoader ? '<div class="hourglass"></div>' : (isUser ? text.replace(/\n/g, '<br>') : formatAiText(text));
    const messageElement = document.createElement('div');
    messageElement.className = className;
    messageElement.innerHTML = `<div class="message-text">${content}</div>`;
    if (messagesContainer) {
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    return messageElement;
}

if (sendBtn) {
    sendBtn.addEventListener('click', async () => {
        const text = inputArea.value.trim();
        if (!text) return;
        appendMessage(text, true);
        inputArea.value = '';
        inputArea.style.height = '40px';
        const loader = appendMessage('', false, true);
        try {
            const response = await fetch("https://new-1-5155.onrender.com/api/chat", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            const data = await response.json();
            loader.remove();
            appendMessage(data.text, false);
        } catch (e) {
            loader.remove();
            appendMessage("Ошибка соединения.", false);
        }
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch("https://new-1-5155.onrender.com/api/history");
        const history = await response.json();
        if (messagesContainer) {
            messagesContainer.innerHTML = ""; 
            history.forEach(msg => appendMessage(msg.content || msg.text, msg.role === 'user'));
        }
    } catch (e) { console.error(e); }
});
