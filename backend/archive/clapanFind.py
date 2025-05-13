import psycopg2
from prettytable import PrettyTable

db_config = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'Neh,byf66',
    'host': 'localhost',
    'port': '5432'
}


def find_BP_clapans(turbine_name: str):
    conn, cursor, count_found, BP_by_ID, ID_and_name = None, None, None, [], {}
    drawing_numbers, valves_all_info = [], []

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # SQL-запрос для выборки всех чертежей клапанов, связанных с указанной турбиной
        query_get_drawings = """
        SELECT Чертеж_клапана 
        FROM "Base"
        WHERE Турбина = %s
        """

        cursor.execute(query_get_drawings, (turbine_name,))
        drawings = cursor.fetchall()

        # Если чертежи не найдены, выводим сообщение об этом
        if not drawings:
            print(f"Чертежи для турбины '{turbine_name}' не найдены.")
        else:
            # Считаем количество найденных чертежей и сохраняем их номера
            count_found = len(drawings)
            drawing_numbers = [drawing[0] for drawing in drawings if drawing[0] is not None]

            trash = ", ".join(drawing_numbers)
            print(f"Чертежи клапанов для турбины '{turbine_name}': {trash}")

            # Создаем таблицу для отображения данных о клапанах
            headers = ["ID", "Источник", "Проверено", "Проверяющий", "Тип клапана", "Чертеж клапана",
                       "Количество участков", "Чертеж буксы", "Чертеж штока", "Диаметр штока", "Точность штока",
                       "Точность буксы", "Расчетный зазор", "Длина участка 1", "Длина участка 2", "Длина участка 3",
                       "Длина участка 4", "Длина участка 5", "Радиус скругления"]
            table = PrettyTable()
            table.field_names = headers

            # Для каждого найденного чертежа получаем информацию о клапанах
            for drawing_number in drawing_numbers:
                # SQL-запрос для выборки данных о клапанах по номеру чертежа
                query_get_valve_info = """
                SELECT * 
                FROM "Stock"
                WHERE Чертеж_клапана = %s
                """

                # Выполняем запрос и получаем результат
                cursor.execute(query_get_valve_info, (drawing_number,))
                valve_info = cursor.fetchall()

                # Если информация о клапанах найдена, добавляем её в таблицу и в список
                if valve_info:
                    for info in valve_info:
                        info = [int(info[0]), *info[1:]]
                        BP_by_ID.append(info[0])
                        ID_and_name[info[0]] = info[5]
                        table.add_row(info)
                        valves_all_info.append(info)

            # Выводим таблицу с информацией о клапанах
            print(table)

    except psycopg2.Error as e:
        # В случае ошибки подключения или выполнения запроса выводим сообщение об ошибке
        print(f"Ошибка базы данных: {e}")

    finally:
        # Закрываем курсор и соединение с базой данных
        if conn:
            cursor.close()
            conn.close()

    # Возвращаем количество найденных чертежей, все данные о клапанах, идентификаторы чертежей и их названия
    return count_found, valves_all_info, BP_by_ID, ID_and_name
