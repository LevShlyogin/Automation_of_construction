from typing import Any
from calculations.clapanFind import find_BP_clapans


def entry_database() -> tuple[Any, int, list[Any]]:
    # Бесконечный цикл для запроса названия турбины у пользователя
    while True:
        turbin_name = input("Введите название турбины: ")
        count_finded, BPs_infos, BP_by_ID, ID_and_name = find_BP_clapans(
            turbin_name)  # Вызов функции для поиска чертежей
        # Формируем строку с айди и именами чертежей
        str_id_name = ', '.join(f"{key} - {value}" for key, value in ID_and_name.items())
        if BP_by_ID:
            break

    # Бесконечный цикл для запроса интересующего айди чертежа у пользователя
    while True:
        print(f"Найдено {count_finded} чертеж(а/ей), с {len(BP_by_ID)} запис(ями/ью) о них: {str_id_name}")
        needed_BPs = int(input("Введите интересующий вас айди чертежа: "))
        if needed_BPs in ID_and_name.keys():
            BPsNeededInfo = BPs_infos[[*ID_and_name.keys()].index(needed_BPs)]
            print("Информация о чертеже: ", BPsNeededInfo, sep="\n")
            break
        else:
            print("\Чертеж с таким айди не найден среди чертежей выбранной турбины."
                  "\nПожалуйста пересмотрите список найденных чертежей.\n")

    # Возвращаем количество найденных чертежей, айди выбранного чертежа и список некоторых данных о чертеже
    return count_finded, needed_BPs, [BPsNeededInfo[4], BPsNeededInfo[6], *BPsNeededInfo[9:]]
