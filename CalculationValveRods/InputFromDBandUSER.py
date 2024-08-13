# Импортируем функцию из файла ClapansByTurbin.py
from CalculationValveRods.DATABASE.ClapansByTurbin import find_BP_clapans

turbin_name = input("Введите название турбины: ")
BPs, BPs_infos = find_BP_clapans(turbin_name)

needed_BPs = input(f"Найдено {len(BPs)} чертеж(а/ей): ")
