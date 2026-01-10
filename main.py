import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

app = FastAPI()

# 1. ГАРАНТИРОВАННОЕ ОПРЕДЕЛЕНИЕ ПУТИ
# Находим папку, в которой лежит текущий файл main.py
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

# Проверка в консоли при запуске
if not os.path.exists(static_dir):
    print(f"❌ ОШИБКА: Папка не найдена по пути: {static_dir}")
    print(f"Проверьте, что папка 'static' находится в {current_dir}")
else:
    print(f"✅ УСПЕХ: Статика обнаружена в: {static_dir}")

# 2. ДАННЫЕ (ОСТАЕМСЯ НА ПРЕЖНЕЙ ЛОГИКЕ)
class User(BaseModel):
    lastName: str
    firstName: str
    middleName: str = ""
    position: str
    mailRequired: bool

@app.get("/api/positions")
async def get_pos():
    return ["DevOps Engineer", "Backend Developer", "Product Manager"]

@app.post("/api/register")
async def register(user: User):
    return {"status": "success", "login": f"{user.lastName.lower()}.test"}

# 3. МОНТИРОВАНИЕ (Теперь с абсолютным путем)
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "index.html not found inside static folder"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)