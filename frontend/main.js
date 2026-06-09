const form = document.getElementById("form");
const input = document.getElementById("input");
const messages = document.getElementById("messages");

const imageBtn = document.getElementById("imageBtn");
const imageInput = document.getElementById("imageInput");

const loginScreen = document.getElementById("loginScreen");
const loginInput = document.getElementById("loginInput");
const loginBtn = document.getElementById("loginBtn");

let selectedImageBase64 = null;
let userName = null;

// =====================
// LOGIN
// =====================
loginBtn.addEventListener("click", () => {
    const value = loginInput.value.trim();
    if (!value) return;

    userName = value;
    loginScreen.style.display = "none";
});

// =====================
// IMAGE
// =====================
imageBtn.addEventListener("click", () => {
    imageInput.click();
});

imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onload = () => {
        selectedImageBase64 = reader.result;
        addMessage("📷 изображение", "user", selectedImageBase64);
    };

    reader.readAsDataURL(file);
});

// =====================
// SEND
// =====================
form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const text = input.value.trim();
    if (!text && !selectedImageBase64) return;

    addMessage(text || "📷 изображение", "user", selectedImageBase64);

    try {
        // Указываем полный адрес бэкенда для связи двух сервисов на Render
        const res = await fetch("https://new-1-5155.onrender.com/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                text: text || "[image]" // Заменили message на text, чтобы бэкенд его понял
            })
        });

        if (!res.ok) {
            throw new Error("Ошибка сервера");
        }

        const data = await res.json();

        // Берем ответ из поля text, которое возвращает наш бэкенд
        addMessage(data.text || "⚠️ пустой ответ", "bot");

    } catch (err) {
        addMessage("❌ Нет соединения с сервером", "bot");
    }

    input.value = "";
    selectedImageBase64 = null;
    imageInput.value = "";
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

    const safeText = (text === undefined || text === null) ? "" : String(text);
    p.innerHTML = marked.parse(safeText);

    div.appendChild(p);

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}
