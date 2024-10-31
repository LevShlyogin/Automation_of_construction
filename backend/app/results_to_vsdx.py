from vsdx import VisioFile


def create_valve_diagram(calculation_result, valve_info):
    """
    Создает схему клапана на основе реальных расчетов и параметров клапана

    Parameters:
    calculation_result (dict): результаты расчётов (например, давления, температуры и т.д.)
    valve_info (ValveInfo): информация о клапане (например, диаметр, высота и т.д.)

    Returns:
    str: имя файла сгенерированной схемы
    """
    num_sections = len(calculation_result["Gi"])  # Количество участков
    num_outlets = len(calculation_result["ejector_props"])  # Количество отсосов

    # Проверка диапазонов
    if not (2 <= num_sections <= 5):
        raise ValueError("Количество участков должно быть от 2 до 5")
    if not (1 <= num_outlets <= 4):
        raise ValueError("Количество отсосов должно быть от 1 до 4")

    # Открываем существующий шаблон Visio-документа
    vis = VisioFile('template.vsdx')  # Убедитесь, что у вас есть файл-шаблон template.vsdx
    page = vis.pages[0]  # Используем первую страницу для добавления элементов

    # Функция для рисования секции клапана
    def draw_section(x_start, y_start, section_height, section_width, outlets, section_index):
        # Найдём фигуру на странице, которую будем использовать для секции
        shape_master = page.shapes[0]  # Предположим, что первая фигура на странице - это шаблон секции

        # Добавляем новую фигуру на основе шаблона
        new_shape = shape_master.copy(page)  # Копируем фигуру на ту же страницу

        # Перемещаем фигуру в нужное место
        new_shape.move(x_start, y_start)

        # Обновляем текст фигуры на основании расчётов
        new_shape.text = f"Секция {section_index + 1}\nP={calculation_result['Pi_in'][section_index]:.2f}\nH={calculation_result['Hi'][section_index]:.2f}"

        # Расчет позиций отсосов и добавление текста
        outlet_spacing = section_height / (outlets + 1)
        for i in range(outlets):
            y_pos = y_start + outlet_spacing * (i + 1)
            pressure = calculation_result["ejector_props"][i]["P"]
            enthalpy = calculation_result["ejector_props"][i]["H"]
            page.add_textbox(f"P{i + 1}={pressure:.2f}\nH{i + 1}={enthalpy:.2f}", x_start + section_width + 25, y_pos)

        # Добавление текста с размерами
        diameter = valve_info.diameter
        delta = 0.2  # Примерное значение, можно заменить на реальное
        page.add_textbox(f"D={diameter}\ndelt={delta:.2f}", x_start, y_start + section_height + 10)

    # Параметры для размещения схемы
    start_x = 50
    start_y = 50
    section_spacing = 200  # Расстояние между секциями
    base_section_height = 300
    base_section_width = 50

    # Создание участков клапана
    for i in range(num_sections):
        # Расчет количества отсосов для текущей секции
        section_outlets = min(num_outlets, i + 1)

        # Рисование секции
        draw_section(
            start_x + i * section_spacing,
            start_y,
            base_section_height,
            base_section_width - i * 5,  # Уменьшаем ширину каждой следующей секции
            section_outlets,
            i
        )

    # Добавление общей подписи
    page.add_textbox("L, D, delt - мм\nP - кгс/см2\nH - ккал/кг", start_x, start_y - 50)

    # Сохранение файла
    filename = f"valve_diagram_{valve_info.name}.vsdx"
    vis.save_vsdx(filename)
    return filename