// =====================
// SEND
// =====================
form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const text = input.value.trim();
    if (!text && !selectedImageBase64) return;

    addMessage(text || "📷 изображение", "user", selectedImageBase64);

    try {
        const res = await fetch("https://new-1-5155.onrender.com/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                text: text // Отправляем именно 'text', так как бэкенд теперь ждет его
            })
        });

        if (!res.ok) {
            throw new Error("Ошибка сервера");
        }

        const data = await res.json();

        // Отображаем ответ, который пришел в поле 'text'
        addMessage(data.text || "⚠️ пустой ответ", "bot");

    } catch (err) {
        addMessage("❌ Ошибка: " + err.message, "bot");
    }

    input.value = "";
    selectedImageBase64 = null;
    imageInput.value = "";
});
