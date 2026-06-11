const form = document.getElementById("form");
const input = document.getElementById("input");
const messages = document.getElementById("messages");
const imageBtn = document.getElementById("imageBtn");
const imageInput = document.getElementById("imageInput");
const loginScreen = document.getElementById("loginScreen");
const loginInput = document.getElementById("loginInput");
const loginBtn = document.getElementById("loginBtn");

const clearTimer = document.getElementById("clearTimer");

let selectedImageBase64 = null;
let userName = null;
let clearTimeoutId = null;
let currentController = null;

// =====================
// LOGIN
// =====================
loginBtn.addEventListener("click", () => {
    const value = loginInput.value.trim();
    if (!value) {
        alert("Введите имя!");
        return;
    }

    userName = value;
    loginScreen.style.display = "none";
});

// =====================
// CLEAR CHAT
// =====================
function clearChat() {
    messages.innerHTML = "";
}

function startClearTimer(minutes) {
    if (clearTimeoutId) {
        clearTimeout(clearTimeoutId);
        clearTimeoutId = null;
    }

    clearTimeoutId = setTimeout(() => {
        clearChat();
        clearTimeoutId = null;
    }, minutes * 60 * 1000);
}

if (clearTimer) {
    clearTimer.value = "60";
    startClearTimer(60);

    clearTimer.addEventListener("change", () => {
        const value = clearTimer.value;
        if (value === "now") {
            clearChat();
            return;
        }
        if (!value) return;
        const minutes = parseInt(value);
        if (!isNaN(minutes)) {
            startClearTimer(minutes);
        }
    });
}

// =====================
// SEND
// =====================
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text && !selectedImageBase64) return;

    addMessage(text, "user", selectedImageBase64);

    input.value = "";
    input.style.height = "auto";
    selectedImageBase64 = null;

    if (currentController) {
        currentController.abort();
        currentController = null;
    }

    currentController = new AbortController();

    try {
        const res = await fetch("https://new-1-5155.onrender.com/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text || "[image]" }),
            signal: currentController.signal
        });

        if (!res.ok) throw new Error("Ошибка сервера");
        const data = await res.json();
        addMessage(data.text, "bot");
    } catch (err) {
        if (err.name !== "AbortError") {
            addMessage("❌ Ошибка соединения", "bot");
        }
    } finally {
        currentController = null;
    }
});

// =====================
// UI
// =====================
function addMessage(text, type, image = null) {
    const div = document.createElement("div");
    div.className = `message ${type === "user" ? "user-msg" : "bot-msg"}`;

    if (image) {
        const img = document.createElement("img");
        img.src = image;
        img.style.maxWidth = "200px";
        img.style.borderRadius = "10px";
        div.appendChild(img);
    }

    const contentDiv = document.createElement("div");
    contentDiv.innerHTML = marked.parse(text || "");
    div.appendChild(contentDiv);

    // Контейнер для кнопок
    const header = document.createElement("div");
    header.className = "message-header";

    // Кнопка копирования
    const copyBtn = document.createElement("button");
    copyBtn.className = "action-btn";
    copyBtn.innerHTML = "📋";
    copyBtn.title = "Копировать";
    copyBtn.onclick = () => {
        navigator.clipboard.writeText(text).then(() => {
            alert("Скопировано!");
        });
    };
    header.appendChild(copyBtn);

    // Кнопка редактирования (только для юзера)
    if (type === "user") {
        const editBtn = document.createElement("button");
        editBtn.className = "action-btn";
        editBtn.innerHTML = "✏️";
        editBtn.title = "Редактировать";
        editBtn.onclick = () => {
            input.value = text;
            const next = div.nextElementSibling;
            if (next && next.classList.contains("bot-msg")) next.remove();
            div.remove();
            if (currentController) {
                currentController.abort();
                currentController = null;
            }
            input.focus();
        };
        header.appendChild(editBtn);
    }

    div.appendChild(header);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}
