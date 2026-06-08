const form = document.getElementById("form");
const input = document.getElementById("input");
const messages = document.getElementById("messages");

const imageBtn = document.getElementById("imageBtn");
const imageInput = document.getElementById("imageInput");

let selectedImageBase64 = null;

// =====================
// ОТКРЫТЬ ФАЙЛЫ
// =====================
imageBtn.addEventListener("click", () => {
    imageInput.click();
});

// =====================
// ЧТЕНИЕ ФАЙЛА
// =====================
imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];

    if (!file) return;

    const reader = new FileReader();

    reader.onload = () => {
        selectedImageBase64 = reader.result;

        addMessage("Вы выбрали изображение 📷", "user", selectedImageBase64);
    };

    reader.readAsDataURL(file);
});

// =====================
// ОТПРАВКА СООБЩЕНИЯ
// =====================
form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const text = input.value.trim();

    if (!text && !selectedImageBase64) return;

    addMessage(text || "📷 изображение", "user", selectedImageBase64);

    const payload = {
        message: text || "[image]",
        image: selectedImageBase64
    };

    input.value = "";
    selectedImageBase64 = null;
    imageInput.value = "";

    const res = await fetch("/api/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    const data = await res.json();

    addMessage(data.reply, "bot");
});

// =====================
// UI ФУНКЦИЯ
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
    p.innerHTML = marked.parse(text);

    div.appendChild(p);

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}
