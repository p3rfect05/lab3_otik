import struct

# Ваша сигнатура формата (6 байт)
SIGNATURE = b'MYARCH'  # Можно выбрать любые 6 байтов


# Кодер: создаем архив R из файла Q
def encode(input_file, output_file):
    with open(input_file, 'rb') as f:
        file_data = f.read()

    file_size = len(file_data)

    # Формируем архивный файл
    with open(output_file, 'wb') as f:
        # Записываем сигнатуру (6 байт)
        f.write(SIGNATURE)
        # Записываем версию формата (2 байта, беззнаковое короткое целое, версия = 0)
        f.write(struct.pack('H', 0))  # H означает unsigned short (2 байта)
        # Записываем длину исходного файла (8 байт, беззнаковое длинное целое)
        f.write(struct.pack('Q', file_size))  # Q означает unsigned long long (8 байт)
        # Записываем "сырые" данные исходного файла
        f.write(file_data)
    print(f"Файл {input_file} успешно заархивирован в {output_file}")


# Декодер: восстанавливаем файл Q из архива R
def decode(input_archive, output_file):
    with open(input_archive, 'rb') as f:
        # Читаем и проверяем сигнатуру
        signature = f.read(6)
        if signature != SIGNATURE:
            print("Ошибка: неверная сигнатура файла!")
            return

        # Читаем и проверяем версию формата
        version = struct.unpack('H', f.read(2))[0]
        if version != 0:
            print("Ошибка: неподдерживаемая версия формата!")
            return

        # Читаем длину исходного файла
        file_size = struct.unpack('Q', f.read(8))[0]

        # Читаем "сырые" данные исходного файла
        file_data = f.read(file_size)

        # Восстанавливаем исходный файл
        with open(output_file, 'wb') as out_f:
            out_f.write(file_data)

    print(f"Архив {input_archive} успешно разархивирован в {output_file}")


# Пример использования:
encode('', 'archive.myarch')  # Кодирование файла example.txt в archive.myarch
decode('archive_v2.myarch', '')  # Декодирование в restored_example.txt
