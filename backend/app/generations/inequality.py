import random
import sympy as sp


def generate_inequality(level):
    signs = ['<', '>', '<=', '>=']
    x = sp.symbols('x')
    if level == 1:
        num = random.randint(1, 10)
        result = random.randint(1, 20)
        sign = random.choice(signs)
        return f"x + {num} {sign} {result}", f"x {sign} {result - num}"
    elif level == 2:
        num = random.randint(10, 20)
        result = random.randint(10, 60)
        sign = random.choice(signs)
        return f"x * {num} {sign} {result}", f"x {sign} {sp.solve(num * x - result)[0]}"
    else:  # 3
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        c = random.randint(1, 10)
        sign = random.choice(['<', '>', '<=', '>='])
        # Решение квадратного неравенства через дискриминант
        discriminant = b ** 2 - 4 * a * c
        if discriminant > 0:
            x1, x2 = sp.solve(a * x ** 2 + b * x + c)
            # x1 = sp.solve(-b + sp.sqrt(discriminant) / (2 * a))
            # x2 = sp.solve(-b - sp.sqrt(discriminant) / (2 * a))
            if a > 0:
                if sign in ['>', '>=']:
                    if sign == '>=':
                        return f"{a}x^2 + {b}x + {c} {sign} 0", f"x <= {x1} или x >= {x2}"
                    else:
                        return f"{a}x^2 + {b}x + {c} {sign} 0", f"x < {x1} или x > {x2}"
                else:
                    if sign == '<=':
                        return f"{a}x^2 + {b}x + {c} {sign} 0", f"{x1} <= x <= {x2}"
                    else:
                        return f"{a}x^2 + {b}x + {c} {sign} 0", f"{x1} < x < {x2}"
            else:
                if sign in ['>', '>=']:
                    return f"{a}x^2 + {b}x + {c} {sign} 0", "нет решения"
                else:
                    return f"{a}x^2 + {b}x + {c} {sign} 0", "все x"
        else:
            if a > 0:
                if sign in ['>', '>=']:
                    return f"{a}x^2 + {b}x + {c} {sign} 0", "все x"
                else:
                    return f"{a}x^2 + {b}x + {c} {sign} 0", "нет решения"
            else:
                if sign in ['>', '>=']:
                    return f"{a}x^2 + {b}x + {c} {sign} 0", "нет решения"
                else:
                    return f"{a}x^2 + {b}x + {c} {sign} 0", "все x"
