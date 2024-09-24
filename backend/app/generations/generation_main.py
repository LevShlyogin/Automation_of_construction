from app.generations.equation import generate_equation
from app.generations.inequality import generate_inequality
from app.generations.numerical import generate_numerical

import random
import sympy as sp


# Главная функция для выбора типа и сложности примера
def generate_example(difficulty=None, example_type=None, operations=None):
    if difficulty is None:
        difficulty = random.choice([1, 2, 3])
    if example_type is None:
        example_type = random.choice(['числовые примеры', 'уравнения', 'неравенства'])

    if example_type == 'числовые примеры':
        question, answer = generate_numerical(difficulty, operations)
    elif example_type == 'уравнения':
        question, answer = generate_equation(difficulty, operations)
    else:  # неравенства
        question, answer = generate_inequality(difficulty)

    return str(question), answer, difficulty


# Функция для проверки ответа пользователя
def check_answer(user_answer, correct_answer):
    if type(correct_answer) is list:
        if [user_answer.split()] == correct_answer:
            return True
        elif str(correct_answer) == user_answer.strip():
            return True
    elif str(correct_answer) == user_answer.strip():
        return True
    return False
