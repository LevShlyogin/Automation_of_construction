import logging
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, computed_field
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Модель данных для входных параметров
class ValveInfo(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    diameter: Optional[float] = None
    clearance: Optional[float] = None
    count_parts: Optional[int] = None
    len_part1: Optional[float] = None
    len_part2: Optional[float] = None
    len_part3: Optional[float] = None
    len_part4: Optional[float] = None
    len_part5: Optional[float] = None
    round_radius: Optional[float] = None

    @computed_field
    @property
    def section_lengths(self) -> List[Optional[float]]:
        return [
            self.len_part1,
            self.len_part2,
            self.len_part3,
            self.len_part4,
            self.len_part5
        ]


# Класс для работы с XML-файлами diagrams.net
class DiagramModifier:
    """Класс для парсинга, модификации и сохранения XML-схем diagrams.net."""

    def __init__(self, template_path: str):
        """
        Инициализация модификатора диаграмм.

        Args:
            template_path (str): Путь к исходному XML-файлу шаблона.
        """
        self.template_path = template_path
        self.tree: Optional[ET.ElementTree] = None
        self.root: Optional[ET.Element] = None
        self._load_template()

    def _load_template(self) -> None:
        """Загружает XML-шаблон из файла."""
        try:
            self.tree = ET.parse(self.template_path)
            self.root = self.tree.getroot()
            logger.info(f"Шаблон XML успешно загружен из {self.template_path}")
        except ET.ParseError as e:
            logger.error(f"Ошибка парсинга XML-файла: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка парсинга XML-файла: {e}")
        except FileNotFoundError:
            logger.error(f"Файл шаблона {self.template_path} не найден")
            raise HTTPException(status_code=404, detail=f"Файл шаблона {self.template_path} не найден")

    def update_parameter(self, cell_id: str, new_value: str) -> None:
        """
        Обновляет значение параметра в элементе <mxCell> по его id.

        Args:
            cell_id (str): Идентификатор элемента <mxCell>.
            new_value (str): Новое значение параметра (включая HTML-форматирование).
        """
        if not self.root:
            raise ValueError("XML-шаблон не загружен")

        # Находим элемент <mxCell> по id
        cell = self.root.find(f".//mxCell[@id='{cell_id}']")
        if cell is None:
            logger.warning(f"Элемент с id={cell_id} не найден в XML")
            return

        # Обновляем атрибут value
        cell.set("value", new_value)
        logger.info(f"Обновлён параметр в элементе с id={cell_id}: {new_value}")

    def save_modified_diagram(self, output_path: str) -> None:
        """
        Сохраняет изменённый XML-файл.

        Args:
            output_path (str): Путь для сохранения изменённого файла.
        """
        if not self.tree:
            raise ValueError("XML-шаблон не загружен")

        try:
            self.tree.write(output_path, encoding="utf-8", xml_declaration=True)
            logger.info(f"Изменённый XML-файл сохранён по пути: {output_path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения XML-файла: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка сохранения XML-файла: {e}")


# Класс для сопоставления параметров ValveInfo с элементами XML
class ParameterMapper:
    """Класс для сопоставления параметров модели ValveInfo с элементами XML."""

    def __init__(self, count_parts: int):
        """
        Инициализация маппера параметров.

        Args:
            count_parts (int): Количество частей клапана, определяет, какие параметры мапятся.
        """
        self.count_parts = count_parts
        # Базовое сопоставление параметров (может быть расширено для каждого шаблона)
        self.mapping: Dict[str, Dict[str, Any]] = {
            "clearance": {
                "cell_id": f"clearance_{count_parts}_parts",
                "label": "delt",
                "format": lambda x: f"{x:.2f}" if x is not None else None
            },
            "diameter": {
                "cell_id": f"diameter_{count_parts}_parts",
                "label": "D",
                "format": lambda x: f"{int(x)}" if x is not None else None
            },
            "round_radius": {
                "cell_id": f"round_radius_{count_parts}_parts",
                "label": "R",
                "format": lambda x: f"{x:.2f}" if x is not None else None
            }
        }
        # Добавляем маппинг для длин секций в зависимости от count_parts
        for i in range(1, count_parts + 1):
            self.mapping[f"len_part{i}"] = {
                "cell_id": f"len_part{i}_{count_parts}_parts",
                "label": f"L{i}",
                "format": lambda x: f"{int(x)}" if x is not None else None
            }

    def get_html_value(self, label: str, formatted_value: str) -> str:
        """        Формирует HTML-строку для атрибута value в <mxCell>.

        Args:
            label (str): Название параметра (например, 'delt', 'D').
            formatted_value (str): Отформатированное значение параметра.

        Returns:
            str: HTML-строка для атрибута value.
        """
        return (
            f'<font style="font-size: 18px;" face="Times New Roman">'
            f'<b style="">{label} = {formatted_value}</b>'
            f'</font>'
        )

    def map_parameters(self, valve_info: ValveInfo) -> Dict[str, str]:
        """
        Сопоставляет параметры ValveInfo с элементами XML.

        Args:
            valve_info (ValveInfo): Объект с параметрами клапана.

        Returns:
            Dict[str, str]: Словарь, где ключ — id элемента <mxCell>, значение — HTML-строка для атрибута value.
        """
        updates = {}
        valve_dict = valve_info.model_dump()

        for param_name, config in self.mapping.items():
            value = valve_dict.get(param_name)
            if value is not None:
                formatted_value = config["format"](value)
                html_value = self.get_html_value(config["label"], formatted_value)
                updates[config["cell_id"]] = html_value

        return updates


# Класс для генерации итогового файла
class DiagramGenerator:
    """Класс для генерации итогового XML-файла на основе шаблона и параметров."""

    def __init__(self, templates_dir: str, output_dir: str):
        """
        Инициализация генератора диаграмм.

        Args:
            templates_dir (str): Директория с шаблонами XML.
            output_dir (str): Директория для сохранения сгенерированных файлов.
        """
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        # Сопоставление count_parts с путями к шаблонам
        self.template_mapping = {
            2: os.path.join(templates_dir, "template_2_parts.xml"),
            3: os.path.join(templates_dir, "template_3_parts.xml"),
            4: os.path.join(templates_dir, "template_4_parts.xml"),
            5: os.path.join(templates_dir, "template_5_parts.xml")
        }

    def _validate_count_parts(self, count_parts: Optional[int]) -> int:
        """
        Проверяет корректность значения count_parts.

        Args:
            count_parts (Optional[int]): Количество частей клапана.

        Returns:
            int: Проверенное значение count_parts.

        Raises:
            HTTPException: Если count_parts недопустимое.
        """
        if count_parts is None:
            logger.error("Параметр count_parts не указан")
            raise HTTPException(status_code=400, detail="Параметр count_parts обязателен")
        if count_parts == 1:
            logger.error("Количество частей не может быть равно 1")
            raise HTTPException(status_code=400, detail="Количество частей не может быть равно 1")
        if count_parts not in self.template_mapping:
            logger.error(f"Недопустимое количество частей: {count_parts}. Допустимые значения: 2, 3, 4, 5")
            raise HTTPException(
                status_code=400,
                detail=f"Недопустимое количество частей: {count_parts}. Допустимые значения: 2, 3, 4, 5"
            )
        return count_parts

    def _get_template_path(self, count_parts: int) -> str:
        """
        Возвращает путь к шаблону на основе count_parts.

        Args:
            count_parts (int): Количество частей клапана.

        Returns:
            str: Путь к соответствующему шаблону.
        """
        template_path = self.template_mapping[count_parts]
        if not os.path.exists(template_path):
            logger.error(f"Шаблон для {count_parts} частей не найден: {template_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Шаблон для {count_parts} частей не найден"
            )
        return template_path

    def generate_diagram(self, valve_info: ValveInfo) -> str:
        """
        Генерирует XML-файл с обновлёнными параметрами.

        Args:
            valve_info (ValveInfo): Объект с параметрами клапана.

        Returns:
            str: Путь к сгенерированному файлу.

        Raises:
            HTTPException: Если произошла ошибка при генерации файла.
        """
        # Валидация count_parts
        count_parts = self._validate_count_parts(valve_info.count_parts)

        # Получаем путь к соответствующему шаблону
        template_path = self._get_template_path(count_parts)

        # Инициализируем модификатор с выбранным шаблоном
        modifier = DiagramModifier(template_path)

        # Инициализируем маппер параметров
        mapper = ParameterMapper(count_parts)

        # Сопоставляем параметры с элементами XML
        updates = mapper.map_parameters(valve_info)

        # Обновляем параметры в XML
        for cell_id, html_value in updates.items():
            modifier.update_parameter(cell_id, html_value)

        # Генерируем уникальное имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"scheme_{count_parts}_parts_{timestamp}.drawio"
        output_path = os.path.join(self.output_dir, output_filename)

        # Сохраняем изменённый файл
        modifier.save_modified_diagram(output_path)

        return output_path


# Инициализация FastAPI
app = FastAPI(title="Valve Diagram Generator")

# Путь к директории с шаблонами и директория для выходных файлов
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(APP_ROOT, "drawio_templates")  # Папка с шаблонами
OUTPUT_DIR = os.path.join(APP_ROOT, "generated_diagrams")  # Временная папка

# Инициализация генератора
generator = DiagramGenerator(TEMPLATES_DIR, OUTPUT_DIR)


@app.post("/generate_scheme", response_class=FileResponse)
async def generate_scheme(valve_info: ValveInfo):
    """
    Эндпоинт для генерации XML-схемы с обновлёнными параметрами.

    Args:
        valve_info (ValveInfo): Объект с параметрами клапана.

    Returns:
        FileResponse: Сгенерированный XML-файл для скачивания.

    Raises:
        HTTPException: Если произошла ошибка при генерации файла.
    """
    try:
        # Генерируем XML-файл с обновлёнными параметрами
        output_path = generator.generate_diagram(valve_info)

        # Проверяем, что файл был создан
        if not os.path.exists(output_path):
            logger.error(f"Файл {output_path} не был создан")
            raise HTTPException(status_code=500, detail="Ошибка генерации XML-файла")

        # Возвращаем файл для скачивания
        return FileResponse(
            path=output_path,
            media_type="application/xml",
            filename=os.path.basename(output_path),
            headers={"Content-Disposition": f"attachment; filename={os.path.basename(output_path)}"}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Ошибка при генерации схемы: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации схемы: {e}")


# Пример использования через curl или HTTP-клиент
if __name__ == "__main__":
    import uvicorn
    import requests
    import json

    # Запуск сервера (для тестирования)
    uvicorn.run(app, host="0.0.0.0", port=8000)

    # Пример запроса через Python requests
    url = "http://localhost:8000/generate_scheme"
    payload = {
        "count_parts": 3,
        "clearance": 0.45,
        "diameter": 60.0,
        "len_part1": 200.0,
        "len_part2": 120.0,
        "len_part3": 150.0,
        "round_radius": 5.0
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, data=json.dumps(payload), headers=headers)

    if response.status_code == 200:
        with open("downloaded_scheme.xml", "wb") as f:
            f.write(response.content)
        print("Файл успешно скачан как downloaded_scheme.xml")
    else:
        print(f"Ошибка: {response.status_code}, {response.text}")
