import unittest
from unittest.mock import patch, Mock
import sys
import os

# Добавляем корневую директорию проекта в PYTHONPATH для возможности импорта 'schemas'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from schemas import CalculationParams, ValveInfo, TurbineInfo


class TestValveCalculator(unittest.TestCase):
    @patch('backend.app.core.config.Settings')  # Путь к Settings
    @patch('backend.app.utils.calculate_enthalpy_for_air', return_value=100.0)
    @patch('backend.app.utils.convert_to_meters', side_effect=lambda x, y: x)
    @patch('backend.app.utils.ph2v', return_value=10.0)
    @patch('backend.app.utils.ph2t', return_value=350.0)
    @patch('backend.app.utils.ph', return_value=100.0)
    @patch('backend.app.utils.pt2h', return_value=200.0)
    @patch('backend.app.utils.ksi_calc', return_value=1.5)
    @patch('backend.app.utils.part_props_detection', return_value=50.0)
    @patch('backend.app.utils.convert_pressure_to_mpa', return_value=0.1)
    @patch('backend.app.utils.air_calc', return_value=5.0)
    @patch('backend.app.utils.handle_error', side_effect=Exception("Handle Error Called"))
    def test_initialization(self,
                            mock_handle_error,
                            mock_air_calc,
                            mock_convert_pressure_to_mpa,
                            mock_part_props_detection,
                            mock_ksi_calc,
                            mock_pt2h,
                            mock_ph,
                            mock_ph2t,
                            mock_ph2v,
                            mock_convert_to_meters,
                            mock_calculate_enthalpy_for_air,
                            mock_settings):
        # Настраиваем мок-экземпляр Settings
        mock_settings_instance = Mock()
        mock_settings_instance.PROJECT_NAME = "Test Project"
        mock_settings_instance.POSTGRES_SERVER = "localhost"
        mock_settings_instance.POSTGRES_USER = "test_user"
        mock_settings_instance.POSTGRES_PASSWORD = "test_password"
        mock_settings_instance.FIRST_SUPERUSER = "admin@example.com"
        mock_settings_instance.FIRST_SUPERUSER_PASSWORD = "admin_password"
        mock_settings_instance.SENTRY_DSN = None
        mock_settings_instance.BACKEND_CORS_ORIGINS = []
        mock_settings_instance.SQLALCHEMY_DATABASE_URI = "postgresql://test_user:test_password@localhost/test_db"
        mock_settings_instance.FRONTEND_HOST = "http://localhost:5173"
        mock_settings_instance.ENVIRONMENT = "local"
        mock_settings_instance.SMTP_HOST = "smtp.example.com"
        mock_settings_instance.EMAILS_FROM_EMAIL = "no-reply@example.com"
        mock_settings_instance.EMAILS_FROM_NAME = "Test Project"
        mock_settings_instance.PG_PORT = 5432
        mock_settings_instance.PG_DB = "test_db"
        mock_settings_instance.SMTP_TLS = True
        mock_settings_instance.SMTP_SSL = False
        mock_settings_instance.SMTP_PORT = 587
        mock_settings_instance.SMTP_USER = None
        mock_settings_instance.SMTP_PASSWORD = None
        mock_settings_instance.EMAIL_RESET_TOKEN_EXPIRE_HOURS = 48
        mock_settings_instance.EMAIL_TEST_USER = "test@example.com"
        # Добавьте любые другие необходимые поля
        mock_settings.return_value = mock_settings_instance

        # Импортируем ValveCalculator внутри патча
        from backend.app.utils import ValveCalculator

        # Создаём экземпляр ValveCalculator
        calculator = ValveCalculator(self.params, self.valve_info)

        # Проверяем начальные значения
        self.assertEqual(calculator.temperature_start_DB, 300.0)
        self.assertEqual(calculator.t_air, 25.0)
        self.assertEqual(calculator.h_air, 100.0)
        self.assertEqual(calculator.count_valves, 2)

        self.assertEqual(calculator.radius_rounding, 0.05)
        self.assertEqual(calculator.delta_clearance, 0.01)
        self.assertEqual(calculator.diameter_stock, 0.02)
        self.assertEqual(calculator.len_parts, [1.0, 1.5, 2.0, 2.5, 3.0])

        self.assertEqual(calculator.count_parts, 5)
        self.assertEqual(calculator.p_suctions, [1.0, 0.9, 0.8, 0.7])
        self.assertEqual(calculator.P_values, [1.0, 1.1, 1.2, 1.3, 1.4])
        self.assertEqual(calculator.p_deaerator, 1.1)

        self.assertEqual(calculator.len_parts_extended, [1.0, 1.5, 2.0, 2.5, 3.0])
        self.assertEqual(calculator.len_part1, 1.0)
        self.assertEqual(calculator.len_part2, 1.5)
        self.assertEqual(calculator.len_part3, 2.0)
        self.assertEqual(calculator.len_part4, 2.5)
        self.assertEqual(calculator.len_part5, 3.0)

        self.assertAlmostEqual(calculator.proportional_coef, 0.05 / (0.01 * 2))
        self.assertAlmostEqual(calculator.S, 0.01 * 3.141592653589793 * 0.02)
        self.assertEqual(calculator.enthalpy_steam, 200.0)
        self.assertEqual(calculator.KSI, 1.5)

        # Проверка начальных значений G, T, H
        self.assertEqual(calculator.G_part1, 0.0)
        self.assertEqual(calculator.G_part2, 0.0)
        self.assertEqual(calculator.G_part3, 0.0)
        self.assertEqual(calculator.G_part4, 0.0)
        self.assertEqual(calculator.G_part5, 0.0)

        self.assertEqual(calculator.t_part1, 0.0)
        self.assertEqual(calculator.t_part2, 0.0)
        self.assertEqual(calculator.t_part3, 0.0)
        self.assertEqual(calculator.t_part4, 0.0)
        self.assertEqual(calculator.t_part5, 0.0)

        self.assertEqual(calculator.h_part1, 0.0)
        self.assertEqual(calculator.h_part2, 0.0)
        self.assertEqual(calculator.h_part3, 0.0)
        self.assertEqual(calculator.h_part4, 0.0)
        self.assertEqual(calculator.h_part5, 0.0)

        # Инициализация дополнительных атрибутов
        self.assertIsNone(calculator.v_part1)
        self.assertIsNone(calculator.din_vis_part1)
        self.assertIsNone(calculator.v_part2)
        self.assertIsNone(calculator.din_vis_part2)
        self.assertIsNone(calculator.v_part3)
        self.assertIsNone(calculator.din_vis_part3)
        self.assertIsNone(calculator.v_part4)
        self.assertIsNone(calculator.din_vis_part4)
        self.assertIsNone(calculator.v_part5)
        self.assertIsNone(calculator.din_vis_part5)
        self.assertIsNone(calculator.p_ejector)

    # Другие тесты можно добавить аналогичным образом

    if __name__ == '__main__':
        unittest.main()