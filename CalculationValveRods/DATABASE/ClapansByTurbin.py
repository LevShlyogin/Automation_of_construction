from itertools import count

import psycopg2
from prettytable import PrettyTable

# Установите параметры подключения к базе данных
db_config = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'Neh,byf66',
    'host': 'localhost',
    'port': '5432'  # Обычно 5432
}


def find_BP_clapans(turbine_name: str):
    conn, cursor, drawing_numbers, valves_all_info = None, None, None, None
    count_found, BP_by_ID, ID_and_name = None, [], {}

    try:
        # Подключение к базе данных
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # SQL-запрос для получения чертежей клапанов по турбине
        query_get_drawings = """
        SELECT Чертеж_клапана 
        FROM "Base"
        WHERE Турбина = %s
        """

        # Выполнение первого запроса
        cursor.execute(query_get_drawings, (turbine_name,))
        drawings = cursor.fetchall()

        count_found = len(drawings)

        if not drawings:
            print(f"Чертежи для турбины '{turbine_name}' не найдены.")
        else:
            drawing_numbers = [drawing[0] for drawing in drawings]
            trash = ", ".join(drawing_numbers)
            print(f"Чертежи клапанов для турбины '{turbine_name}': {trash}")

            # Создание таблицы
            headers = ["ID", "Источник", "Проверено", "Проверяющий", "Тип клапана", "Чертеж клапана",
                       "Количество участков", "Чертеж буксы", "Чертеж штока", "Диаметр штока", "Точность штока",
                       "Точность буксы", "Расчетный зазор", "Длина участка 1", "Длина участка 2", "Длина участка 3",
                       "Длина участка 4", "Длина участка 5", "Радиус скругления"]
            table = PrettyTable()
            table.field_names = headers

            valves_all_info = []
            counter = 1

            for drawing_number in drawing_numbers:
                # SQL-запрос для получения данных о клапане из таблицы "Stock"
                query_get_valve_info = """
                SELECT * 
                FROM "Stock"
                WHERE Чертеж_клапана = %s
                """

                # Выполнение второго запроса
                cursor.execute(query_get_valve_info, (drawing_number,))
                valve_info = cursor.fetchall()

                if valve_info:
                    for info in valve_info:
                        info = [int(info[0]), *info[1::]]
                        BP_by_ID.append(info[0])
                        ID_and_name[info[0]] = info[5]
                        # Убираем номер чертежа из данных о клапане
                        table.add_row(info)
                        valves_all_info.append(info)
                        counter += 1

            print(table)

    except psycopg2.Error as e:
        print(f"Ошибка базы данных: {e}")
    finally:
        # Закрытие соединения с базой данных
        if conn:
            cursor.close()
            conn.close()

    return count_found, valves_all_info, BP_by_ID, ID_and_name
