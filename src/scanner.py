"""Рекурсивный обход папки и сохранение индекса в SQLite.

Обход дерева написан вручную: функция _walk вызывает саму себя для каждой
вложенной папки (рекурсия), а не использует готовый os.walk.
"""

import os
from datetime import datetime, timezone
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


def _walk(current, root, result):
    """Рекурсивно обходит папку current, складывая файлы в список result.

    Для каждой вложенной папки функция вызывает саму себя (рекурсия) —
    «проваливается» на уровень ниже. root нужен, чтобы считать путь
    относительным от корня сканирования, result — общий накопитель файлов.
    """
    try:
        entries = list(os.scandir(current))
    except OSError:
        return
    for entry in entries:
        if entry.is_dir(follow_symlinks=False):
            _walk(Path(entry.path), root, result)      # рекурсивный вызов — спускаемся в подпапку
        elif entry.is_file(follow_symlinks=False):
            try:
                st = entry.stat()
            except OSError:
                continue
            full = Path(entry.path)
            ext = full.suffix.lower()
            result.append({
                "rel_path": full.relative_to(root).as_posix(),
                "size": st.st_size,
                "mtime": st.st_mtime,
                "ext": ext,
                "file_type": file_type(ext),
            })


def scan_folder(root):
    """Возвращает список метаданных всех файлов папки (обход — ручной рекурсией).

    Пути в индексе относительные — относительно корня сканирования.
    """
    root = Path(root)
    result = []
    _walk(root, root, result)
    return result


def save_index(conn, files, root):
    """Обновляет индекс в SQLite по результатам сканирования.

    Новые файлы добавляются, существующие обновляются, а записи, которых
    больше нет в папке, помечаются как 'missing'. Так индекс всегда отражает
    текущее состояние выбранной папки.
    """
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    seen = set()
    for f in files:
        seen.add(f["rel_path"])
        conn.execute(
            """
            INSERT INTO files (rel_path, size, mtime, ext, file_type, status, scanned_at)
            VALUES (:rel_path, :size, :mtime, :ext, :file_type, 'present', :scanned_at)
            ON CONFLICT(rel_path) DO UPDATE SET
                size       = excluded.size,
                mtime      = excluded.mtime,
                ext        = excluded.ext,
                file_type  = excluded.file_type,
                status     = 'present',
                scanned_at = excluded.scanned_at
            """,
            {**f, "scanned_at": now},
        )
    for row in conn.execute("SELECT rel_path FROM files WHERE status='present'").fetchall():
        if row["rel_path"] not in seen:
            conn.execute("UPDATE files SET status='missing' WHERE rel_path=?", (row["rel_path"],))
    conn.execute(
        "INSERT INTO scans (root, started_at, files_seen) VALUES (?, ?, ?)",
        (str(Path(root).resolve()), now, len(files)),
    )
    conn.commit()
