from backend.models.turbine import TurbineParameters

def calculate_efficiency(parameters: TurbineParameters) -> float:
    # Реализация логики расчетов
    return (parameters.pressure * parameters.temperature) / parameters.flow_rate