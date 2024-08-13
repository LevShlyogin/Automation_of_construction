# Импортируем функцию из файла ClapansByTurbin.py
from CalculationValveRods.DATABASE.ClapansByTurbin import find_BP_clapans

turbin_name = input("Введите название турбины: ")
BPs, BPs_infos = find_BP_clapans(turbin_name)

print(f"Найдено {len(BPs)} чертеж(а/ей): {" , ".join(BPs)}")
needed_BPs = input("Введите интересующий вас чертеж: ")

if needed_BPs in BPs:
    print("CONGRATULATIONS", BPs_infos[BPs.index(needed_BPs)], sep="\n")
else:
    print("\nДанный чертеж не найден среди чертежей выбранной турбины."
          "\nПожалуйста пересмотрите список найденных чертежей.")
