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

        const res = await fetch(
            "https://new-1-5155.onrender.com/api/chat",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    text: text || "[image]"
                }),
                signal: currentController.signal
            }
        );

        if (!res.ok) {
            throw new Error("Ошибка сервера");
        }

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

    // =====================
    // EDIT BUTTON
    // =====================
    if (type === "user") {

        const oldButtons =
            messages.querySelectorAll(".edit-btn");

        oldButtons.forEach(btn => btn.remove());

        const editBtn = document.createElement("button");

        editBtn.className = "edit-btn";

        editBtn.innerHTML = `
<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
<path
d="M16.862 3.487a2.25 2.25 0 013.182 3.182L8.25 18.463 4 19.5l1.037-4.25L16.862 3.487z"
stroke="currentColor"
stroke-width="2"
stroke-linecap="round"
stroke-linejoin="round"/>
</svg>
`;

        editBtn.style.background = "transparent";
        editBtn.style.border = "none";
        editBtn.style.color = "#9ca3af";
        editBtn.style.cursor = "pointer";

        editBtn.style.display = "block";
        editBtn.style.marginLeft = "auto";
        editBtn.style.marginTop = "6px";
        editBtn.style.padding = "0";

        editBtn.style.opacity = "0";
        editBtn.style.transition = "opacity 0.25s ease";

        setTimeout(() => {
            editBtn.style.opacity = "1";
        }, 50);

        editBtn.onclick = () => {

            input.value = text;

            const next = div.nextElementSibling;

            if (
                next &&
                next.classList.contains("msg") &&
                next.classList.contains("bot")
            ) {
                next.remove();
            }

            div.remove();

            if (currentController) {
                currentController.abort();
                currentController = null;
            }

            input.focus();
        };

        div.appendChild(editBtn);
    }

    messages.appendChild(div);

    messages.scrollTop =
        messages.scrollHeight;
}
