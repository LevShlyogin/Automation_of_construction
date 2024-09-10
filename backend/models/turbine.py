from pydantic import BaseModel

class TurbineParameters(BaseModel):
    name: str
    stocks_list: dict
    pressure: float
    temperature: float
    flow_rate: float