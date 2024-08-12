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

    # SQL-запрос для получения информации о клапанах
    query = """
    SELECT b.Турбина, s.Чертеж_клапана 
    FROM Base b
    JOIN Stock s ON b.Чертеж_клапана = s.Чертеж_клапана
    WHERE b.Турбина = %s
    """

    # Выполнение запроса
    cursor.execute(query, (turbine_name,))
    results = cursor.fetchall()

    if results:
        print(f"Клапаны для турбины '{turbine_name}':")
        for row in results:
            print(f"- Чертеж клапана: {row[1]}")
    else:
        print(f"Клапаны для турбины '{turbine_name}' не найдены.")

except psycopg2.Error as e:
    print(f"Ошибка базы данных: {e}")
    print(f"SQL-запрос: {query}")
    print(f"Параметры запроса: {turbine_name}")
finally:
    # Закрытие соединения с базой данных
    if conn:
        cursor.close()
        conn.close()
