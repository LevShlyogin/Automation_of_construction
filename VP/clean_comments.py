def remove_comments(source_file, dest_file):
    with open(source_file, 'r', encoding='utf-8') as f_in, open(dest_file, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            # Удаляем всё после первого неэкранированного #
            parts = []
            escape = False
            for char in line:
                if char == '#' and not escape:
                    break
                escape = (char == '\\') and not escape  # Учитываем экранирование
                parts.append(char)
            cleaned_line = ''.join(parts).rstrip() + '\n'
            f_out.write(cleaned_line)


name_file = input("Напишите название файла в этой же папке:\n")
remove_comments(name_file, f'{name_file}_cleaned.py')
