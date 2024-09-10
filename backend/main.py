from fastapi import FastAPI
from backend.api.endpoints import router as api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

'''
У меня есть репозиторий от старых наработок с регистрацией, 
реализованной на FastAPI, можно его использовать как базу 
для авторизации пользователей
'''

# Настройка CORS, если потребуется
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Или укажите конкретные домены для безопасности
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов
app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Steam Turbine Calculator API"}