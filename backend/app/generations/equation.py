import random
import sympy as sp


def generate_equation(level, operations=None):
    x = sp.symbols('x')
    if operations is None:
        operations = ['+', '-', '*', '/']
    else:
        operations = " ".join(operations).split()
    if level == 1:
        num = random.randint(1, 20)
        result = random.randint(1, 20)
    elif level == 2:
        num = random.randint(10, 50)
        result = random.randint(10, 50)
    else:  # 3
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        c = random.randint(1, 10)
        # Решение квадратного уравнения через дискриминант
        discriminant = b ** 2 - 4 * a * c
        if discriminant > 0:
            x1, x2 = sp.solve(a * x ** 2 + b * x + c)
            return f"{a}x^2 + {b}x + {c} = 0", f"x1 = {x1} ; x2 = {x2}"
        elif discriminant == 0:
            x = sp.solve(a * x ** 2 + b * x + c)[0]
            return f"{a}x^2 + {b}x + {c} = 0", str(x)
        else:
            return f"{a}x^2 + {b}x + {c} = 0", "нет реальных корней"
    operation = random.choice(operations)
    if operation == "+":
        ans = result - num
    elif operation == "-":
        ans = result + num
    elif operation == "*":
        ans = sp.solve(num * x - result)[0]
    else:
        ans = sp.solve(x / num - result)[0]
    return f"x {operation} {num} = {result}", ans
