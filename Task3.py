import struct

# Сигнатура формата (6 байт) из ЛЗ.№1
SIGNATURE = b'MYARCH'

# Константы для формата сжатия и защиты от помех
NO_COMPRESSION = 0
NO_PROTECTION = 0

# Версия формата ЛЗ.№3
FORMAT_VERSION = (1, 1)  # Версия 1.1 (1 - мажорная, 1 - минорная)


# Кодер: создание архива R из файла Q по формату ЛЗ.№3
def encode(input_file, output_file, compression=NO_COMPRESSION, protection=NO_PROTECTION):
    with open(input_file, 'rb') as f:
        file_data = f.read()

    file_size = len(file_data)

    # Создаем архивный файл
    with open(output_file, 'wb') as f:
        # Записываем сигнатуру (6 байт)
        f.write(SIGNATURE)
        # Записываем версию формата (1 байт для мажорной версии и 1 байт для минорной)
        f.write(struct.pack('B', FORMAT_VERSION[0]))  # B = unsigned char (1 байт)
        f.write(struct.pack('B', FORMAT_VERSION[1]))
        # Записываем коды сжатия и защиты от помех (по 1 байту на каждый)
        f.write(struct.pack('B', compression))
        f.write(struct.pack('B', protection))
        # Записываем длину исходного файла (8 байт, беззнаковое длинное целое)
        f.write(struct.pack('Q', file_size))  # Q = unsigned long long (8 байт)
        # Записываем "сырые" данные исходного файла
        f.write(file_data)

    print(f"Файл {input_file} успешно заархивирован в {output_file}")


# Декодер: восстановление файла Q из архива R по формату ЛЗ.№3
def decode(input_archive, output_file):
    with open(input_archive, 'rb') as f:
        # Читаем и проверяем сигнатуру
        signature = f.read(6)
        if signature != SIGNATURE:
            print("Ошибка: неверная сигнатура файла!")
            return

        # Читаем версию формата
        major_version = struct.unpack('B', f.read(1))[0]
        minor_version = struct.unpack('B', f.read(1))[0]
        print(f"Версия формата: {major_version}.{minor_version}")

        # Читаем коды сжатия и защиты от помех
        compression = struct.unpack('B', f.read(1))[0]
        protection = struct.unpack('B', f.read(1))[0]
        print(f"Алгоритм сжатия: {compression}, Защита от помех: {protection}")

        # Читаем длину исходного файла
        file_size = struct.unpack('Q', f.read(8))[0]

        # Читаем "сырые" данные исходного файла
        file_data = f.read(file_size)

        # Восстанавливаем исходный файл
        with open(output_file, 'wb') as out_f:
            out_f.write(file_data)

    print(f"Архив {input_archive} успешно разархивирован в {output_file}")


# Пример использования:
encode('example.txt', 'archive_v3.myarch')  # Кодирование файла example.txt в archive_v3.myarch
decode('archive_v3.myarch', 'restored_example.txt')  # Декодирование в restored_example.txt
