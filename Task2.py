import os
import struct

# Сигнатура формата (6 байт) из ЛЗ.№1
SIGNATURE = b'MYARCH'

# Константы для формата сжатия и защиты от помех
NO_COMPRESSION = 0
NO_PROTECTION = 0

# Версия формата ЛЗ.№2
FORMAT_VERSION = (1, 1)  # Версия 1.1 (1 - мажорная, 1 - минорная)


# Функция для рекурсивного получения всех файлов и папок
def get_files_and_folders(root_dir):
    file_list = []
    for root, dirs, files in os.walk(root_dir):
        for directory in dirs:
            dir_path = os.path.relpath(os.path.join(root, directory), root_dir)
            file_list.append((dir_path, 1, 0))  # Папка, тип = 1, размер = 0
        for file in files:
            file_path = os.path.relpath(os.path.join(root, file), root_dir)
            file_size = os.path.getsize(os.path.join(root_dir, file_path))
            file_list.append((file_path, 0, file_size))  # Файл, тип = 0, указываем размер
    return file_list


# Кодер: архивирует несколько файлов и папок
def encode(input_dir, output_file, compression=NO_COMPRESSION, protection=NO_PROTECTION):
    files_and_folders = get_files_and_folders(input_dir)

    with open(output_file, 'wb') as f:
        # Записываем сигнатуру (6 байт)
        f.write(SIGNATURE)
        # Записываем версию формата (1 байт для мажорной версии и 1 байт для минорной)
        f.write(struct.pack('B', FORMAT_VERSION[0]))  # B = unsigned char (1 байт)
        f.write(struct.pack('B', FORMAT_VERSION[1]))
        # Записываем коды сжатия и защиты от помех (по 1 байту на каждый)
        f.write(struct.pack('B', compression))
        f.write(struct.pack('B', protection))
        # Записываем количество файлов и папок (4 байта, беззнаковое целое)
        f.write(struct.pack('I', len(files_and_folders)))  # I = unsigned int (4 байта)

        # Записываем метаданные для каждого файла/папки
        for file_path, file_type, file_size in files_and_folders:
            # Записываем длину пути и сам путь (длина + строка)
            encoded_path = file_path.encode('utf-8')
            f.write(struct.pack('H', len(encoded_path)))  # H = unsigned short (2 байта)
            f.write(encoded_path)
            # Записываем тип (1 байт: 0 для файла, 1 для папки)
            f.write(struct.pack('B', file_type))
            # Записываем размер файла (8 байт, 0 для папок)
            f.write(struct.pack('Q', file_size))

        # Записываем данные файлов
        for file_path, file_type, file_size in files_and_folders:
            if file_type == 0:  # Если это файл
                with open(os.path.join(input_dir, file_path), 'rb') as infile:
                    f.write(infile.read())

    print(f"Директория {input_dir} успешно заархивирована в {output_file}")


# Декодер: восстанавливает файлы и папки из архива
def decode(input_archive, output_dir):
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

        # Читаем количество файлов/папок
        num_files = struct.unpack('I', f.read(4))[0]
        print(f"Количество файлов/папок: {num_files}")

        file_info = []

        # Читаем метаданные для каждого файла/папки
        for _ in range(num_files):
            # Читаем длину пути
            path_length = struct.unpack('H', f.read(2))[0]
            # Читаем путь
            file_path = f.read(path_length).decode('utf-8')
            # Читаем тип (1 байт)
            file_type = struct.unpack('B', f.read(1))[0]
            # Читаем размер файла (8 байт)
            file_size = struct.unpack('Q', f.read(8))[0]
            file_info.append((file_path, file_type, file_size))

        # Восстанавливаем файлы и папки
        for file_path, file_type, file_size in file_info:
            output_path = os.path.join(output_dir, file_path)
            if file_type == 1:  # Это папка
                os.makedirs(output_path, exist_ok=True)
            else:  # Это файл
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as outfile:
                    outfile.write(f.read(file_size))

    print(f"Архив {input_archive} успешно разархивирован в директорию {output_dir}")


# Пример использования:
input_file_format = 'example.txt'
encode(input_file_format, 'archive_v2.myarch')  # Архивирование директории test_dir в файл archive_v2.myarch
decode('archive_v2.myarch', 'restored_' + input_file_format)  # Декодирование в директорию restored_dir
