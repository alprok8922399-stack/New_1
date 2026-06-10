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

if (clearTimer) {
    clearTimer.addEventListener("change", () => {

        if (clearTimeoutId) {
            clearTimeout(clearTimeoutId);
            clearTimeoutId = null;
        }

        const value = clearTimer.value;

        if (value === "now") {
            clearChat();
            return;
        }

        if (!value) return;

        const minutes = parseInt(value);

        if (!isNaN(minutes)) {
            clearTimeoutId = setTimeout(() => {
                clearChat();
                clearTimeoutId = null;
            }, minutes * 60 * 1000);
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

    try {
        const res = await fetch("https://new-1-5155.onrender.com/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                text: text || "[image]"
            })
        });

        if (!res.ok) {
            throw new Error("Ошибка сервера");
        }

        const data = await res.json();

        addMessage(data.text, "bot");

    } catch (err) {

        addMessage("❌ Ошибка соединения", "bot");

    }
});

// =====================
// UI
// =====================
function addMessage(text, type, image = null) {

    const div = document.createElement("div");

    div.className =
        type === "user"
            ? "msg user"
            : "msg bot";

    if (image) {

        const img = document.createElement("img");

        img.src = image;
        img.style.maxWidth = "200px";
        img.style.borderRadius = "10px";

        div.appendChild(img);
    }

    const p = document.createElement("div");

    p.innerHTML = marked.parse(text || "");

    div.appendChild(p);

    messages.appendChild(div);

    messages.scrollTop = messages.scrollHeight;
}
