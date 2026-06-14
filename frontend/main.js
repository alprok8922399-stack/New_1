document.addEventListener("DOMContentLoaded", () => {
    const inputArea = document.querySelector(".input-area");
    const messagesDiv = document.querySelector(".messages");
    const serverUrl = "https://new-1-5155.onrender.com";

    // Функция для отображения сообщений
    function renderMessage(msg, role) {
        let cls = "";
        if (role === "user") cls = "msg user";
        else cls = "msg bot";

        const div = document.createElement("div");
        div.classList.add(cls);
        div.textContent = msg;
        messagesDiv.appendChild(div);
        scrollToBottom();
    }

    // Прокрутка вниз
    function scrollToBottom() {
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    // Загрузка истории при старте
    fetch(`${serverUrl}/api/history`)
        .then(response => response.json())
        .then(history => {
            console.log("История:", history);
            history.forEach(msg => {
                renderMessage(msg.content, msg.role);
            });
        })
        .catch(error => console.error("Ошибка при получении истории:", error));

    // Обработка формы
    inputArea.addEventListener("submit", async event => {
        event.preventDefault(); // Отмена стандартной отправки формы

        const inputField = document.getElementById("input");
        const userMsg = inputField.value.trim();

        if (!userMsg) return;

        // Показываем сообщение пользователя
        renderMessage(userMsg, "user");
        inputField.value = ""; // Очищаем поле

        // Отправляем на сервер
        const data = { message: userMsg };
        const options = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        };

        const res = await fetch(`${serverUrl}/api/chat`, options);
        const result = await res.json();

        if (result.response) {
            renderMessage(result.response, "bot");
        } else {
            renderMessage(`Ошибка: ${result.error}`, "bot");
        }
    });
});
