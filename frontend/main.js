const messagesContainer = document.querySelector('.messages');
const inputArea = document.getElementById('input');

// Находим кнопки гарантированно: скрепку по ID, а отправить — как вторую кнопку в блоке
const attachBtn = document.getElementById('attach-btn');
const fileInput = document.getElementById('file-input');
const sendBtn = document.querySelector('.input-area button:not(#attach-btn)'); 

const previewContainer = document.getElementById('image-preview-container');
const imagePreview = document.getElementById('image-preview');
const cancelImageBtn = document.getElementById('cancel-image-btn');

let selectedImageBase64 = "";

const BACKEND_URL = "https://new-1-5155.onrender.com/api/chat";

// Нажатие на скрепку открывает выбор файлов, и НИЧЕГО не отправляет!
attachBtn.addEventListener('click', (e) => {
    e.preventDefault();
    fileInput.click();
});

// Когда файл выбран
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(event) {
        selectedImageBase64 = event.target.result;
        imagePreview.src = selectedImageBase64;
        previewContainer.style.display = "flex";
    };
    reader.readAsDataURL(file);
});

// Сброс картинки
cancelImageBtn.addEventListener('click', (e) => {
    e.preventDefault();
    clearImageSelection();
});

function clearImageSelection() {
    selectedImageBase64 = "";
    fileInput.value = "";
    previewContainer.style.display = "none";
}

// Добавление сообщения на экран
function appendMessage(text, isUser, imageUrl = "") {
    const messageDiv = document.createElement('div');
    messageDiv.className = isUser ? 'message user' : 'message bot'; 
    messageDiv.style.margin = "10px";
    messageDiv.style.padding = "10px";
    messageDiv.style.borderRadius = "8px";
    messageDiv.style.backgroundColor = isUser ? "#007bff" : "#e9ecef";
    messageDiv.style.color = isUser ? "white" : "black";
    messageDiv.style.alignSelf = isUser ? "flex-end" : "flex-start";
    messageDiv.style.maxWidth = "80%";
    
    let content = `<div>${text}</div>`;
    if (imageUrl) {
        content = `<img src="${imageUrl}" style="max-width: 100%; max-height: 200px; border-radius: 6px; display: block; margin-bottom: 5px;">` + content;
    }
    
    messageDiv.innerHTML = content;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Настоящая функция отправки
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

// Привязываем отправку ТОЛЬКО к кнопке отправки и к Enter
if (sendBtn) {
    sendBtn.addEventListener('click', (e) => {
        e.preventDefault();
        sendMessage();
    });
}

inputArea.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
