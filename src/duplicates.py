"""Подсчёт хэшей файлов и поиск дубликатов."""

import hashlib
from pathlib import Path

_CHUNK = 65536  # читаем файл кусками, чтобы не грузить целиком в память


def file_hash(path):
    """Считает SHA-256 содержимого файла."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(_CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
