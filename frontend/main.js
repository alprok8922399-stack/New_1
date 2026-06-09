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
    if (!value) { alert("Введите имя!"); return; }
    userName = value;
    loginScreen.style.display = "none";
});

// =====================
// SEND
// =====================
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text && !selectedImageBase64) return;

    // 1. Сразу добавляем сообщение пользователя
    addMessage(text, "user", selectedImageBase64);
    
    // 2. СРАЗУ очищаем поле ввода
    input.value = "";
    input.style.height = "auto"; // сброс высоты
    selectedImageBase64 = null;

    try {
        const res = await fetch("https://new-1-5155.onrender.com/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text || "[image]" })
        });
        
        if (!res.ok) throw new Error("Ошибка сервера");
        const data = await res.json();
        
        // 3. Добавляем ответ бота
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
    div.appendChild(p);
    
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}
