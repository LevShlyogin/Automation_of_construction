# Импортируем функцию из файла ClapansByTurbin.py
from CalculationValveRods.DATABASE.ClapansByTurbin import find_BP_clapans


def entry_to_DB():
    while True:
        turbin_name = input("Введите название турбины: ")
        BPs, BPs_infos = find_BP_clapans(turbin_name)
        print(BPs, BPs_infos)
        if BPs:
            break

    while True:
        print(f"Найдено {len(BPs)} чертеж(а/ей): {" , ".join(BPs)}")
        needed_BPs = input("Введите интересующий вас чертеж: ")
        if needed_BPs in BPs:
            BPsNeededInfo = BPs_infos[BPs.index(needed_BPs)]
            print("Информация о чертеже: ", BPsNeededInfo, sep="\n")
            break
        else:
            print("\nДанный чертеж не найден среди чертежей выбранной турбины."
                  "\nПожалуйста пересмотрите список найденных чертежей.\n")
    return needed_BPs, BPsNeededInfo
