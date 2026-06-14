document.addEventListener("DOMContentLoaded", () => {
    const inputField = document.getElementById("input");
    const sendButton = document.querySelector(".input-area button");
    const messagesDiv = document.querySelector(".messages");
    const serverUrl = "https://new-1-5155.onrender.com";

    // Функция для отображения сообщений (используем твои классы стилей)
    function renderMessage(msg, role, isError = false) {
        let cls = role === "user" ? "message user" : "message bot";
        
        const div = document.createElement("div");
        div.className = cls;
        if (isError) div.style.color = "#ff5252";
        
        // Добавляем красивую разметку с жирным шрифтом
        const senderName = role === "user" ? "Вы" : "Бот";
        div.innerHTML = `<strong>${senderName}:</strong><br>${msg}`;
        
        messagesDiv.appendChild(div);
        scrollToBottom();
    }

    // Прокрутка вниз
    function scrollToBottom() {
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    // Главная функция отправки сообщения
    async function sendMessage() {
        const userMsg = inputField.value.trim();
        if (!userMsg) return;

        // 1. Показываем сообщение пользователя на экране
        renderMessage(userMsg, "user");
        inputField.value = ""; // Очищаем поле ввода
        scrollToBottom();

        // 2. Создаем временную плашку ожидания
        const loadingDiv = document.createElement("div");
        loadingDiv.className = "message bot";
        loadingDiv.style.color = "#aaa";
        loadingDiv.innerHTML = "<strong>Бот:</strong><br>Печатает ответ...";
        messagesDiv.appendChild(loadingDiv);
        scrollToBottom();

        try {
            // 3. Отправляем правильные данные на бэкенд
            const response = await fetch(`${serverUrl}/api/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    text: userMsg, 
                    secret: "test-secret" 
                })
            });
            
            const result = await response.json();
            
            // Удаляем плашку ожидания
            loadingDiv.remove();

            // 4. Проверяем ответ сервера
            if (result.text) {
                renderMessage(result.text, "bot");
            } else {
                renderMessage(result.error || "Неизвестная ошибка сервера", "bot", true);
            }
        } catch (error) {
            // Удаляем плашку ожидания в случае сбоя сети
            loadingDiv.remove();
            renderMessage(`Ошибка связи. Бэкенд на Render просыпается, подожди 30 секунд и попробуй еще раз.`, "bot", true);
            console.error("Ошибка запроса:", error);
        }
    }

    // Привязываем отправку к твоей кнопке
    if (sendButton) {
        sendButton.addEventListener("click", (e) => {
            e.preventDefault();
            sendMessage();
        });
    }

    // Разрешаем отправку по нажатию Enter (но без Shift)
    if (inputField) {
        inputField.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
});
