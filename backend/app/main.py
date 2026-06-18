import os
import httpx
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import psycopg2

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return None
    try:
        conn = psycopg2.connect(db_url, connect_timeout=3)
        return conn
    except Exception as e:
        logger.error(f"Не удалось подключиться к БД: {e}")
        return None

@app.on_event("startup")
def startup_event():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
            logger.info("База данных успешно проверена.")
        except Exception as e:
            logger.error(f"Ошибка при создании таблицы: {e}")

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        user_message = data.get("text") or ""
        image_base64 = data.get("image") or ""
        
        # Жесткий характер: убираем робота, добавляем живого друга
        system_prompt = (
            "Ты — близкий друг и крутой ИИ-помощник Алексея. Твой стиль общения — живой, "
            "свободный, с юмором и иронией, как в реальном разговоре. Никакой официальщины, "
            "никаких фраз 'Чем могу быть полезен' или 'Как я могу помочь'. "
            "Отвечай всегда только на русском языке, просто, емко и по-человечески. "
            "Если Алексей просит шутку — шути смешно, жизненно, избегай избитых шаблонов."
        )

        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO chat_messages (role, content) VALUES (%s, %s)",
                    ("user", user_message)
                )
                conn.commit()
            except Exception as e:
                logger.error(f"Не удалось записать сообщение пользователя: {e}")

        history_messages = []
        if conn:
            try:
                cur.execute("""
                    SELECT role, content 
                    FROM chat_messages 
                    WHERE id < (SELECT MAX(id) FROM chat_messages)
                    ORDER BY id DESC 
                    LIMIT 10
                """)
                rows = cur.fetchall()
                for row in rows[::-1]:
                    history_messages.append({"role": row[0], "content": row[1]})
            except Exception as e:
                logger.error(f"Не удалось достать контекст для ИИ: {e}")

        messages_for_ai = [{"role": "system", "content": system_prompt}]
        messages_for_ai.extend(history_messages)
        
        current_content = [{"type": "text", "text": user_message}]
        if image_base64:
            current_content.append({"type": "image_url", "image_url": {"url": image_base64}})
            
        messages_for_ai.append({"role": "user", "content": current_content})

        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "google/gemini-2.5-flash", 
                    "messages": messages_for_ai,
                    "max_tokens": 1000
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                reply = response.json()['choices'][0]['message']['content']
                
                if conn:
                    try:
                        cur.execute(
                            "INSERT INTO chat_messages (role, content) VALUES (%s, %s)",
                            ("assistant", reply)
                        )
                        conn.commit()
                    except Exception as e:
                        logger.error(f"Не удалось записать ответ ИИ: {e}")
                
                if conn:
                    cur.close()
                    conn.close()

                return {"text": reply}
            else:
                if conn:
                    cur.close()
                    conn.close()
                return {"text": f"Ошибка OpenRouter: {response.text}"}
                
    except Exception as e:
        return {"text": f"Ошибка бэкенда: {str(e)}"}

@app.get("/api/history")
async def get_history():
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor() 
        cur.execute("""
            SELECT id, role, content 
            FROM chat_messages 
            ORDER BY id DESC 
            LIMIT 15
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        if not rows:
            return []
            
        history_summary = []
        for row in rows[::-1]:
            history_summary.append({"id": row[0], "role": row[1], "content": row[2]})
            
        return history_summary
        
    except Exception as e:
        logger.error(f"Ошибка при получении истории: {e}")
        return []

# НОВАЯ ФУНКЦИЯ: Удаление старого сообщения из базы данных по его ID
@app.delete("/api/delete/{msg_id}")
async def delete_message(msg_id: int):
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "message": "Нет подключения к БД"}
    try:
        cur = conn.cursor()
        # Удаляем сообщение с конкретным номером из таблицы
        cur.execute("DELETE FROM chat_messages WHERE id = %s", (msg_id,))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success", "message": f"Сообщение {msg_id} удалено"}
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения {msg_id}: {e}")
        return {"status": "error", "message": str(e)}
