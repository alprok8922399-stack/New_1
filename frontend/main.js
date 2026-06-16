const messagesContainer = document.querySelector('.messages');
const inputArea = document.getElementById('input');
const sendBtn = document.getElementById('send-btn');
const attachBtn = document.getElementById('attach-btn');
const fileInput = document.getElementById('file-input');
const previewContainer = document.getElementById('image-preview-container');
const imagePreview = document.getElementById('image-preview');
const cancelImageBtn = document.getElementById('cancel-image-btn');

let selectedImageBase64 = "";
const BACKEND_URL = "https://new-1-5155.onrender.com/api/chat";
const HISTORY_URL = "https://new-1-5155.onrender.com/api/history"; 

attachBtn.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
        selectedImageBase64 = event.target.result;
        imagePreview.src = selectedImageBase64;
        previewContainer.className = ""; // Показываем превью
    };
    reader.readAsDataURL(file);
});

cancelImageBtn.addEventListener('click', () => {
    selectedImageBase64 = "";
    fileInput.value = "";
    previewContainer.className = "preview-hidden";
});

function appendMessage(text, isUser, imageUrl = "") {
    const messageDiv = document.createElement('div');
    messageDiv.className = isUser ? 'message user' : 'message bot';
    
    let content = `<div>${text}</div>`;
    if (imageUrl) {
        content = `<img src="${imageUrl}" style="max-width: 100%; display: block; margin-bottom: 5px;">` + content;
    }
    
    messageDiv.innerHTML = content;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Умная загрузка стартового приветствия
async function loadChatHistory() {
    try {
        const response = await fetch(HISTORY_URL);
        if (!response.ok) return;
        
        const history = await response.json();
        
        // Очищаем экран, чтобы старая история не мозолила глаза
        messagesContainer.innerHTML = "";
        
        // Выводим только сгенерированное ИИ приветствие
        history.forEach(msg => {
            appendMessage(msg.text, msg.role === 'user');
        });
    } catch (error) {
        console.error("Не удалось загрузить приветствие:", error);
    }
}

async function sendMessage() {
    const text = inputArea.value.trim();
    if (!text && !selectedImageBase64) return;

    appendMessage(text || "Фото", true, selectedImageBase64);
    
    const imageToSend = selectedImageBase64;
    inputArea.value = "";
    previewContainer.className = "preview-hidden"; // Прячем превью после отправки

    try {
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, image: imageToSend })
        });
        const data = await response.json();
        appendMessage(data.text, false);
    } catch (error) {
        appendMessage("Ошибка соединения.", false);
    }
}

// Слушаем нажатие кнопки отправки
sendBtn.addEventListener('click', sendMessage);

// Автоматически запрашиваем умное приветствие при открытии чата на телефоне
document.addEventListener('DOMContentLoaded', loadChatHistory);
