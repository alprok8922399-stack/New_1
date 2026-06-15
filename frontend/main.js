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

// Клик по скрепке открывает галерею/камеру
attachBtn.addEventListener('click', () => {
    fileInput.click();
});

// Когда выбрали фото
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(event) {
        selectedImageBase64 = event.target.result;
        imagePreview.src = selectedImageBase64;
        previewContainer.style.display = "flex"; // Показываем превью
    };
    reader.readAsDataURL(file);
});

// Сброс фото
cancelImageBtn.addEventListener('click', () => {
    clearImageSelection();
});

function clearImageSelection() {
    selectedImageBase64 = "";
    fileInput.value = "";
    previewContainer.style.display = "none";
}

// Добавление сообщения в твои классы
function appendMessage(text, isUser, imageUrl = "") {
    const messageDiv = document.createElement('div');
    // Используем твои стандартные классы (user/bot или left/right, подставь свои если не совпало)
    messageDiv.className = isUser ? 'message user' : 'message bot'; 
    messageDiv.style.margin = "10px";
    messageDiv.style.padding = "10px";
    messageDiv.style.borderRadius = "8px";
    messageDiv.style.backgroundColor = isUser ? "#007bff" : "#e9ecef";
    messageDiv.style.color = isUser ? "white" : "black";
    messageDiv.style.alignSelf = isUser ? "flex-end" : "flex-start";
    
    let content = `<div>${text}</div>`;
    if (imageUrl) {
        content = `<img src="${imageUrl}" style="max-width: 100%; max-height: 200px; border-radius: 6px; display: block; margin-bottom: 5px;">` + content;
    }
    
    messageDiv.innerHTML = content;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Отправка
async function sendMessage() {
    const text = inputArea.value.trim();
    if (!text && !selectedImageBase64) return;

    appendMessage(text || "Фотография", true, selectedImageBase64);
    
    const imageToSend = selectedImageBase64;
    inputArea.value = "";
    clearImageSelection();

    try {
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, image: imageToSend })
        });

        const data = await response.json();
        appendMessage(data.text, false);

    } catch (error) {
        appendMessage("Ошибка соединения с сервером.", false);
        console.error(error);
    }
}

sendBtn.addEventListener('click', sendMessage);
inputArea.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
