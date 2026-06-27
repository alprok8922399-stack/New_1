// Конфигурация бэкенда Render
const API_BASE = "https://chat-ai-backend-y1bt.onrender.com"; // Твой бэкенд URL
const PROTON_EMAIL = "aleksey.prokudin.89@proton.me";       // Твой ProtonMail

let currentMode = "public"; 
let selectedModel = "auto";
let uploadedImageBase64 = "";

const chatContainer = document.getElementById("chat-container");
const messageInput = document.getElementById("message-input");
const btnSend = document.getElementById("btn-send");
const btnClear = document.getElementById("btn-clear");
const btnRoom = document.getElementById("btn-room");
const btnMailMode = document.getElementById("btn-mail-mode");
const chatNameElement = document.getElementById("chat-name");
const previewContainer = document.getElementById("preview-container");
const modelBadges = document.querySelectorAll(".model-badge");

// Элементы модального окна
const modalOverlay = document.getElementById("modal-overlay");
const modalTitle = document.getElementById("modal-title");
const passwordInput = document.getElementById("password-input");
const btnModalCancel = document.getElementById("btn-modal-cancel");
const btnModalSubmit = document.getElementById("btn-modal-submit");

let modalAction = ""; 

// Автоматический скролл вниз
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Автоматическое изменение высоты текстового поля
messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = messageInput.scrollHeight + "px";
});

// Выбор модели
modelBadges.forEach(badge => {
    badge.addEventListener("click", () => {
        modelBadges.forEach(b => b.classList.remove("active"));
        badge.classList.add("active");
        selectedModel = badge.dataset.model;
    });
});

// Загрузка картинок (конвертация в Base64)
document.getElementById("btn-attach").addEventListener("click", () => {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = "image/*";
    fileInput.onchange = e => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = event => {
            uploadedImageBase64 = event.target.result;
            renderPreview(uploadedImageBase64);
        };
        reader.readAsDataURL(file);
    };
    fileInput.click();
});

function renderPreview(base64Data) {
    previewContainer.innerHTML = `
        <div class="preview-box">
            <img src="${base64Data}" alt="Превью">
            <button class="btn-remove-preview" id="btn-clear-preview">×</button>
        </div>
    `;
    document.getElementById("btn-clear-preview").addEventListener("click", () => {
        uploadedImageBase64 = "";
        previewContainer.innerHTML = "";
    });
}

// Форматирование Markdown (жирный, ссылки, списки)
function parseMarkdown(text) {
    if (!text) return "";
    let html = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/`(.*?)`/g, "<code>$1</code>")
        .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');

    const lines = html.split("\n");
    let inList = false;
    let listType = ""; 
    let resultLines = [];

    lines.forEach(line => {
        const bulletMatch = line.match(/^[\s]*[*•-]\s+(.*)/);
        const numMatch = line.match(/^[\s]*\d+\.\s+(.*)/);

        if (bulletMatch) {
            if (!inList || listType !== "ul") {
                if (inList) resultLines.push(`</${listType}>`);
                resultLines.push("<ul>");
                inList = true;
                listType = "ul";
            }
            resultLines.push(`<li>${bulletMatch[1]}</li>`);
        } else if (numMatch) {
            if (!inList || listType !== "ol") {
                if (inList) resultLines.push(`</${listType}>`);
                resultLines.push("<ol>");
                inList = true;
                listType = "ol";
            }
            resultLines.push(`<li>${numMatch[1]}</li>`);
        } else {
            if (inList) {
                resultLines.push(`</${listType}>`);
                inList = false;
                listType = "";
            }
            resultLines.push(line ? `<p>${line}</p>` : "");
        }
    });

    if (inList) resultLines.push(`</${listType}>`);
    return resultLines.join("");
}

// Отображение сообщений на экране
function appendMessage(id, role, text) {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message-wrapper", role);
    if (id) wrapper.dataset.id = id;

    const bubble = document.createElement("div");
    bubble.classList.add("message-bubble");
    bubble.innerHTML = parseMarkdown(text);
    wrapper.appendChild(bubble);

    const meta = document.createElement("div");
    meta.classList.add("message-meta");

    const actions = document.createElement("div");
    actions.classList.add("msg-actions");

    // Иконка Копировать
    const btnCopy = document.createElement("button");
    btnCopy.classList.add("action-icon");
    btnCopy.innerHTML = "📋";
    btnCopy.title = "Копировать";
    btnCopy.onclick = () => {
        navigator.clipboard.writeText(text);
        alert("Скопировано!");
    };
    actions.appendChild(btnCopy);

    // Иконка Редактировать (только для юзера)
    if (role === "user") {
        const btnEdit = document.createElement("button");
        btnEdit.classList.add("action-icon");
        btnEdit.innerHTML = "✏️";
        btnEdit.title = "Редактировать";
        btnEdit.onclick = () => {
            messageInput.value = text;
            messageInput.focus();
            if (id && currentMode === "private") {
                fetch(`${API_BASE}/api/delete/${id}`, { method: "DELETE" });
            }
            wrapper.remove();
        };
        actions.appendChild(btnEdit);
    }

    meta.appendChild(actions);
    wrapper.appendChild(meta);
    chatContainer.appendChild(wrapper);
    scrollToBottom();
}

// Загрузка истории приватной комнаты
async function loadHistory() {
    try {
        const res = await fetch(`${API_BASE}/api/history`);
        const data = await res.json();
        chatContainer.innerHTML = "";
        data.forEach(msg => appendMessage(msg.id, msg.role, msg.content));
    } catch (e) {
        console.error("Ошибка загрузки истории:", e);
    }
}

// Прямая отправка последнего сообщения на Proton через FormSubmit.co
async function sendLastMessageToMail() {
    // Находим все текстовые пузыри сообщений в чате
    const bubbles = chatContainer.querySelectorAll(".message-bubble");
    if (bubbles.length === 0) {
        alert("В чате еще нет сообщений для отправки!");
        return;
    }
    
    // Берем самый последний пузырь на экране
    const lastMessageText = bubbles[bubbles.length - 1].innerText;

    try {
        const response = await fetch(`https://formsubmit.co/ajax/${PROTON_EMAIL}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                "Сообщение": lastMessageText,
                "_subject": "Последнее сообщение из AI Chat",
                "_captcha": "false"
            })
        });

        if (response.ok) {
            alert("Запрос отправлен! Проверь ProtonMail для активации или получения письма.");
        } else {
            alert(`Ошибка отправки. Сервер вернул код: ${response.status}`);
        }
    } catch (error) {
        alert(`Сбой сети при отправке: ${error.message}`);
    }
}

// Отправка сообщения в чат ИИ
async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text && !uploadedImageBase64) return;

    messageInput.value = "";
    messageInput.style.height = "auto";

    const sysTime = new Date().toLocaleString("ru-RU");
    const fullTextForAI = `[Системное инфо. Текущие дата и время: ${sysTime}. Имя собеседника: Алексей] ${text}`;

    appendMessage(null, "user", text || "Отправлено изображение");
    const imgToSend = uploadedImageBase64;
    uploadedImageBase64 = "";
    previewContainer.innerHTML = "";

    try {
        const res = await fetch(`${API_BASE}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                text: fullTextForAI,
                mode: currentMode,
                model: selectedModel,
                image: imgToSend
            })
        });
        const data = await res.json();
        appendMessage(null, "assistant", data.text);
    } catch (e) {
        appendMessage(null, "assistant", "Ошибка связи с сервером бэкенда.");
    }
}

btnSend.addEventListener("click", sendMessage);
messageInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey && window.innerWidth > 768) {
        e.preventDefault();
        sendMessage();
    }
});

// Кнопка Очистить
btnClear.addEventListener("click", async () => {
    if (currentMode === "public") {
        chatContainer.innerHTML = "";
    } else {
        modalAction = "clear";
        modalTitle.innerText = "Введите пароль для очистки истории:";
        passwordInput.value = "";
        modalOverlay.classList.remove("hidden");
    }
});

// Кнопка Смены комнаты
btnRoom.addEventListener("click", () => {
    if (currentMode === "public") {
        modalAction = "enter_private";
        modalTitle.innerText = "Доступ в приватную комнату:";
        passwordInput.value = "";
        modalOverlay.classList.remove("hidden");
    } else {
        currentMode = "public";
        chatNameElement.innerText = "Гостевая комната";
        btnRoom.innerText = "🚪 Войти";
        chatContainer.innerHTML = "";
    }
});

// Кнопка Почты @@@
btnMailMode.addEventListener("click", () => {
    sendLastMessageToMail();
});

// Логика обработки модального окна (пароль)
btnModalCancel.addEventListener("click", () => {
    modalOverlay.classList.add("hidden");
    passwordInput.value = "";
});

btnModalSubmit.addEventListener("click", async () => {
    const pass = passwordInput.value.trim();
    if (pass !== "alprok8922399") {
        alert("Неверный пароль!");
        return;
    }

    modalOverlay.classList.add("hidden");

    if (modalAction === "enter_private") {
        currentMode = "private";
        chatNameElement.innerText = "Friend and Helper";
        btnRoom.innerText = "🚪 Выйти";
        await loadHistory();
    } else if (modalAction === "clear") {
        try {
            const res = await fetch(`${API_BASE}/api/history`);
            const messages = await res.json();
            for (const m of messages) {
                await fetch(`${API_BASE}/api/delete/${m.id}`, { method: "DELETE" });
            }
            chatContainer.innerHTML = "";
            alert("История очищена!");
        } catch (e) {
            alert("Ошибка удаления истории");
        }
    }
});
