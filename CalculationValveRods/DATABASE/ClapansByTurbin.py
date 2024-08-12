import psycopg2

# Установите параметры подключения к базе данных
db_config = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'Neh,byf66',
    'host': 'localhost',
    'port': '5432'  # Обычно 5432
}

try:
    # Подключение к базе данных
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Запрос названия турбины у пользователя
    turbine_name = input("Введите название турбины: ")

    # SQL-запрос для получения чертежей клапанов по турбине
    query_get_drawings = """
    SELECT Чертеж_клапана 
    FROM "Base"
    WHERE Турбина = %s
    """

    # Выполнение первого запроса
    cursor.execute(query_get_drawings, (turbine_name,))
    drawings = cursor.fetchall()

    if not drawings:
        print(f"Чертежи для турбины '{turbine_name}' не найдены.")
    else:
        print(f"Чертежи клапанов для турбины '{turbine_name}':")
        for drawing in drawings:
            drawing_number = drawing[0]

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
                    # Вывод всей информации о клапане
                    print("-------------")
                    print(f"ID: {info[0]}")
                    print(f"Источник: {info[1]}")
                    print(f"Проверено (да/нет): {info[2]}")
                    print(f"Проверяющий: {info[3]}")
                    print(f"Тип клапана: {info[4]}")
                    print(f"Чертеж клапана: {info[5]}")
                    print(f"Количество участков: {info[6]}")
                    print(f"Чертеж буксы: {info[7]}")
                    print(f"Чертеж штока: {info[8]}")
                    print(f"Диаметр штока (мм): {info[9]}")
                    print(f"Точность изготовления штока (мм): {info[10]}")
                    print(f"Точность изготовления буксы (мм): {info[11]}")
                    print(f"Расчетный зазор (мм): {info[12]}")
                    print(f"Длина участка 1 (мм): {info[13]}")
                    print(f"Длина участка 2 (мм): {info[14]}")
                    print(f"Длина участка 3 (мм): {info[15]}")
                    print(f"Длина участка 4 (мм): {info[16]}")
                    print(f"Длина участка 5 (мм): {info[17]}")
                    print(f"Радиус скругления размер фаски (мм): {info[18]}")
            else:
                print(f"Данные для чертежа '{drawing_number}' не найдены.")

except psycopg2.Error as e:
    print(f"Ошибка базы данных: {e}")
finally:
    # Закрытие соединения с базой данных
    if conn:
        cursor.close()
        conn.close()
