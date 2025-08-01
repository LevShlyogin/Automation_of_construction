from xml.etree import ElementTree as ET
from typing import Optional
import os
import datetime
from schemas import ValveInfo


class DiagramGenerator:
    def __init__(self, template_path: str, output_dir: str = "generated_diagrams"):
        self.template_path = template_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _read_template(self) -> tuple[ET.ElementTree, ET.Element]:
        """Читает шаблонный XML-файл."""
        tree = ET.parse(self.template_path)
        root = tree.getroot()
        return tree, root

    def _find_element_by_id(self, root: ET.Element, element_id: str) -> Optional[ET.Element]:
        """Ищет элемент по его id."""
        return root.find(f".//*[@id='BLlBBX38aDmSH4QY8xBm-{element_id}']")

    def _update_parameter(self, element: ET.Element, new_value: float) -> None:
        """Обновляет значение параметра в элементе."""
        current_value = element.get("value")
        if current_value is None:
            raise ValueError("Значение параметра не найдено.")

        # Заменяем старое значение на новое
        new_value_str = str(new_value)
        element.set("value", f"delt = {new_value_str}")

    def generate_diagram(self, valve_info: ValveInfo) -> str:
        """
        Генерирует схему на основе данных о клапане.

        Args:
            valve_info: Данные о клапане.

        Returns:
            Путь к сгенерированному файлу.
        """
        # Чтение шаблона
        tree, root = self._read_template()

        # Обновление параметров
        # Обновление delt (clearance)
        element = self._find_element_by_id(root, "11")
        self._update_parameter(element, valve_info.clearance or 0.0)

        # Обновление D (diameter)
        element = self._find_element_by_id(root, "12")
        self._update_parameter(element, valve_info.diameter or 0.0)

        # Обновление L2 (len_part2)
        element = self._find_element_by_id(root, "13")
        self._update_parameter(element, valve_info.len_part2 or 0.0)

        # Обновление L1 (len_part1)
        element = self._find_element_by_id(root, "14")
        self._update_parameter(element, valve_info.len_part1 or 0.0)

        # Создание уникального имени файла
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(
            self.output_dir,
            f"valve_diagram_{timestamp}.drawio"
        )

        # Сохранение файла
        tree.write(output_file, encoding="utf-8", xml_declaration=True)

        return output_file


# Пример использования:
if __name__ == "__main__":
    # Создание экземпляра Informer
    sample_valve = ValveInfo(
        id=1,
        name="Sample Valve",
        type="type1",
        diameter=40.0,
        clearance=0.25,
        len_part1=200,
        len_part2=100
    )

    # Создание генератора
    generator = DiagramGenerator("/app/templates/template_2_parts.xml")

    # Генерация схемы
    file_path = generator.generate_diagram(sample_valve)
    print(f"Схема сохранена в: {file_path}")
