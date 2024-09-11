from fastapi import FastAPI
from backend.api.endpoints import router as api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="WebWSACalculator",
    description="This is backend for calculator",
    summary="UTZ team developers community.",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Deadpoolio the Amazing",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

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