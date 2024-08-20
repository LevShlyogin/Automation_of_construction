# Импортируем функцию из файла ClapansByTurbin.py
from CalculationValveRods.DATABASE.ClapansByTurbin import find_BP_clapans


def entry_to_DB() -> [int, str, []]:
    while True:
        turbin_name = input("Введите название турбины: ")
        count_finded, BPs, BPs_infos = find_BP_clapans(turbin_name)
        if BPs:
            break

    while True:
        print(f"Найдено {count_finded} чертеж(а/ей): {", ".join(BPs)}")
        needed_BPs = input("Введите интересующий вас чертеж: ")
        if needed_BPs in BPs:
            BPsNeededInfo = BPs_infos[BPs.index(needed_BPs)]
            print("Информация о чертеже: ", BPsNeededInfo, sep="\n")
            break
        else:
            print("\nДанный чертеж не найден среди чертежей выбранной турбины."
                  "\nПожалуйста пересмотрите список найденных чертежей.\n")
    return count_finded, needed_BPs, [BPsNeededInfo[4], BPsNeededInfo[6], *BPsNeededInfo[9:]]
