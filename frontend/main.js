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
    if (!value) { alert("Введите имя!"); return; }
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
    clearTimer.value = "60"; // по умолчанию через 1 час
    startClearTimer(60);

    clearTimer.addEventListener("change", () => {
        const value = clearTimer.value;
        if (currentController) { currentController.abort(); currentController = null; }

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
    const signal = currentController.signal;

    try {
        const res = await fetch("https://new-1-5155.onrender.com/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text || "[image]" }),
            signal
        });

        if (!res.ok) throw new Error("Ошибка сервера");
        const data = await res.json();
        addMessage(data.text, "bot");

    } catch (err) {
        if (err.name === "AbortError") return;
        addMessage("❌ Ошибка соединения", "bot");
    } finally {
        currentController = null;
    }
});

// =====================
// UI
// =====================
function addMessage(text, type, image = null) {
    const div = document.createElement("div");
    div.className = type === "user" ? "msg user" : "msg bot";

    if (image) {
        const img = document.createElement("img");
        img.src = image;
        img.style.maxWidth = "200px";
        img.style.borderRadius = "10px";
        div.appendChild(img);
    }

    const p = document.createElement("div");
    p.innerHTML = marked.parse(text || "");
    p.style.display = "inline-block";
    p.style.verticalAlign = "middle";
    div.appendChild(p);

    // =====================
    // EDIT BUTTON (только для последнего сообщения пользователя)
    // =====================
    if (type === "user") {
        // Удаляем кнопки у других сообщений
        const userMessages = messages.querySelectorAll(".msg.user");
        userMessages.forEach(msg => {
            const btn = msg.querySelector(".edit-btn");
            if (btn) btn.remove();
        });

        const editBtn = document.createElement("button");
        editBtn.className = "edit-btn";
        editBtn.innerHTML = "✏️";
        editBtn.style.border = "1px solid black";
        editBtn.style.background = "transparent";
        editBtn.style.color = "black";
        editBtn.style.fontSize = "16px";
        editBtn.style.cursor = "pointer";
        editBtn.style.marginLeft = "10px";
        editBtn.style.verticalAlign = "middle";
        editBtn.style.float = "right";

        editBtn.onclick = () => {
            input.value = text;

            const next = div.nextSibling;
            if (next && next.classList.contains("msg") && next.classList.contains("bot")) {
                next.remove();
            }
            div.remove();

            if (currentController) { currentController.abort(); currentController = null; }

            input.focus();
            input.scrollIntoView({ behavior: "smooth", block: "center" });
        };

        div.appendChild(editBtn);
    }

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
            }
