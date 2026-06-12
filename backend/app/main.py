@app.post("/api/chat")
def chat(req: ChatRequest):
    if not req.message:
        return {"response": "Пустое сообщение"}

    msg = req.message.lower()

    # простая "логика памяти"
    if "как меня зовут" in msg:
        answer = "Я пока не знаю твоего имени 🙂"
    elif "привет" in msg:
        answer = "Привет! 👋"
    elif "что ты умеешь" in msg:
        answer = "Я простой чат. Пока без ИИ, но уже работаю 🙂"
    else:
        answer = "Я получил: " + req.message

    return {
        "response": "🤖 " + answer
    }
