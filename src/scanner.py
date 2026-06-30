"""Рекурсивный обход папки и сбор метаданных файлов."""

import os
from pathlib import Path

# Сопоставление расширений с укрупнённым типом файла.
_TYPE_MAP = {
    "text": {".txt", ".md", ".csv", ".log", ".json", ".xml", ".ini", ".rst"},
    "image": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"},
    "audio": {".mp3", ".wav", ".flac", ".ogg", ".m4a"},
    "video": {".mp4", ".avi", ".mkv", ".mov", ".webm"},
    "archive": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "code": {".py", ".js", ".ts", ".c", ".cpp", ".java", ".html", ".css", ".sh"},
    "doc": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"},
}


def file_type(ext):
    """Возвращает укрупнённый тип файла по расширению."""
    ext = ext.lower()
    for name, exts in _TYPE_MAP.items():
        if ext in exts:
            return name
    return "other"


def scan_folder(root):
    """Рекурсивно обходит папку и возвращает список метаданных всех файлов.

    Пути в индексе относительные — относительно корня сканирования.
    """
    root = Path(root)
    result = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            full = Path(dirpath) / name
            try:
                st = full.stat()
            except OSError:
                # Битые ссылки и недоступные файлы пропускаем.
                continue
            ext = full.suffix.lower()
            result.append({
                "rel_path": full.relative_to(root).as_posix(),
                "size": st.st_size,
                "mtime": st.st_mtime,
                "ext": ext,
                "file_type": file_type(ext),
            })
    return result
