from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Укажите адрес вашего фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Steam Turbine Calculator API"}

class TurbineParameters(BaseModel):
    pressure: float
    temperature: float
    flow_rate: float

@app.post("/calculate")
def calculate_turbine_properties(parameters: TurbineParameters):
    # Пример простой логики расчета: вы можете заменить это на свою логику
    try:
        efficiency = (parameters.pressure * parameters.temperature) / parameters.flow_rate
        result = {"efficiency": efficiency}
        return result
    except ZeroDivisionError:
        raise HTTPException(status_code=400, detail="Flow rate must not be zero.")