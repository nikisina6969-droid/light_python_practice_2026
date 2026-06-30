"""Рекурсивный обход папки и сохранение индекса в SQLite."""

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
    # Файлы, которые были в индексе, но не встретились при обходе.
    for row in conn.execute("SELECT rel_path FROM files WHERE status = 'present'").fetchall():
        if row["rel_path"] not in seen:
            conn.execute(
                "UPDATE files SET status = 'missing' WHERE rel_path = ?",
                (row["rel_path"],),
            )
    conn.execute(
        "INSERT INTO scans (root, started_at, files_seen) VALUES (?, ?, ?)",
        (str(Path(root).resolve()), now, len(files)),
    )
    conn.commit()
