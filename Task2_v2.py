import os
import struct
import zlib
import binascii

from Task2 import input_file_format

# Сигнатура формата (6 байт)
SIGNATURE = b'MYARCH'

# Константы для формата сжатия и защиты от помех
NO_COMPRESSION = 0
ZLIB_COMPRESSION_WITH_CONTEXT = 1
ZLIB_COMPRESSION_WITHOUT_CONTEXT = 2
NO_PROTECTION = 0
CRC32_PROTECTION = 1

# Версия формата
FORMAT_VERSION = (1, 1)  # Версия 1.1


# Функция для рекурсивного получения всех файлов и папок
def get_files_and_folders(root_dir):
    file_list = []
    if os.path.isfile(root_dir):
        file_size = os.path.getsize(root_dir)
        file_list.append((os.path.basename(root_dir), 0, file_size))  # Тип = 0 (файл)
        print(file_list)
    else:
        for root, dirs, files in os.walk(root_dir):
            for directory in dirs:
                dir_path = os.path.relpath(os.path.join(root, directory), root_dir)
                file_list.append((dir_path, 1, 0))  # Папка, тип = 1, размер = 0
            for file in files:
                file_path = os.path.relpath(os.path.join(root, file), root_dir)
                file_size = os.path.getsize(os.path.join(root_dir, file_path))
                file_list.append((file_path, 0, file_size))  # Файл, тип = 0, указываем размер

    return file_list

def rle_compress(data):
    compressed = bytearray()
    i = 0
    while i < len(data):
        count = 1
        # Считаем количество одинаковых последовательных байтов
        while i + 1 < len(data) and data[i] == data[i + 1] and count < 255:
            count += 1
            i += 1
        # Добавляем байт и количество его повторений
        compressed.append(data[i])
        compressed.append(count)
        i += 1
    return compressed

# Функция сжатия данных
def compress_data(data, compression):
    if compression == ZLIB_COMPRESSION_WITH_CONTEXT:
        return zlib.compress(data)
    elif compression == ZLIB_COMPRESSION_WITHOUT_CONTEXT:  # Допустим, что код 2 обозначает RLE-сжатие
        return rle_compress(data)
    return data  # NO_COMPRESSION


# Функция декомпрессии данных
def rle_decompress(data):
    decompressed = bytearray()
    i = 0
    while i < len(data):
        byte = data[i]       # Получаем байт
        count = data[i + 1]  # Получаем количество повторений
        decompressed.extend([byte] * count)  # Добавляем байт count раз
        i += 2  # Переходим к следующей паре (байт, количество)
    return decompressed

# Обновленная функция декомпрессии данных
def decompress_data(data, compression):
    if compression == ZLIB_COMPRESSION_WITH_CONTEXT:
        return zlib.decompress(data)  # Декомпрессия с учетом контекста (Deflate)
    elif compression == ZLIB_COMPRESSION_WITHOUT_CONTEXT:  # Допустим, что код 2 обозначает RLE-сжатие
        return rle_decompress(data)  # Декомпрессия без учета контекста (RLE)
    return data  # NO_COMPRESSION


# Функция защиты от помех (расчет CRC32)
def calculate_checksum(data, protection):
    if protection == CRC32_PROTECTION:
        return binascii.crc32(data)
    return 0  # NO_PROTECTION


# Кодер: архивирует директории или файлы
def encode(input_path, output_file, compression=NO_COMPRESSION, protection=CRC32_PROTECTION):
    files_and_folders = get_files_and_folders(input_path)

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
        for file_path, file_type, _ in files_and_folders:
            # Записываем длину пути и сам путь (длина + строка)
            encoded_path = file_path.encode('utf-8')
            f.write(struct.pack('H', len(encoded_path)))  # H = unsigned short (2 байта)
            f.write(encoded_path)
            # Записываем тип (1 байт: 0 для файла, 1 для папки)
            f.write(struct.pack('B', file_type))

        # Записываем данные файлов и их сжатые размеры
        if len(files_and_folders) == 1 and files_and_folders[0][0] == input_path:
            with open(file_path, 'rb') as infile:
                raw_data = infile.read()
                compressed_data = compress_data(raw_data, compression)
                checksum = calculate_checksum(raw_data, protection)

                # Записываем контрольную сумму (4 байта)
                f.write(struct.pack('I', checksum))  # CRC32 (если нет защиты, будет 0)

                # Записываем размер сжатых данных (8 байт)
                f.write(struct.pack('Q', len(compressed_data)))  # Размер сжатых данных

                # Записываем сжатые данные
                f.write(compressed_data)
        else:
            for file_path, file_type, _ in files_and_folders:
                if file_type == 0:  # Если это файл
                    with open(os.path.join(input_path, file_path), 'rb') as infile:
                        raw_data = infile.read()
                        compressed_data = compress_data(raw_data, compression)
                        checksum = calculate_checksum(raw_data, protection)

                        # Записываем контрольную сумму (4 байта)
                        f.write(struct.pack('I', checksum))  # CRC32 (если нет защиты, будет 0)

                        # Записываем размер сжатых данных (8 байт)
                        f.write(struct.pack('Q', len(compressed_data)))  # Размер сжатых данных

                        # Записываем сжатые данные
                        f.write(compressed_data)

    print(f"{input_path} успешно заархивировано в {output_file}")


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
            file_info.append((file_path, file_type))

        # Восстанавливаем файлы и папки
        for file_path, file_type in file_info:
            output_path = os.path.join(output_dir, file_path)
            if file_type == 1:  # Это папка
                os.makedirs(output_path, exist_ok=True)
            else:  # Это файл
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                # Читаем контрольную сумму
                checksum = struct.unpack('I', f.read(4))[0]
                # Читаем размер сжатых данных
                compressed_size = struct.unpack('Q', f.read(8))[0]
                # Читаем сжатые данные
                compressed_data = f.read(compressed_size)
                raw_data = decompress_data(compressed_data, compression)

                # Проверка контрольной суммы
                if calculate_checksum(raw_data, protection) != checksum:
                    print(f"Ошибка: контрольная сумма не совпадает для файла {file_path}!")
                    return

                # Записываем данные в файл
                with open(output_path, 'wb') as outfile:
                    outfile.write(raw_data)

    print(f"Архив {input_archive} успешно разархивирован в директорию {output_dir}")


# Пример использования:
# Архивируем директорию или файл
file = 'test_dir'
encode(file, 'archive_v2.myarch', compression=ZLIB_COMPRESSION_WITHOUT_CONTEXT, protection=CRC32_PROTECTION)
# Восстанавливаем директорию или файл из архива
decode('archive_v2.myarch', 'restored_' + file)
