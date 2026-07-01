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


def update_hashes(conn, root):
    """Считает и сохраняет хэши для файлов индекса.

    Хэш пересчитывается только если его ещё нет или файл изменился (по mtime),
    иначе берётся сохранённый ранее — так результаты переиспользуются между
    запусками. Возвращает число реально пересчитанных файлов.
    """
    root = Path(root)
    rows = conn.execute(
        "SELECT rel_path, mtime, hash, hashed_mtime FROM files WHERE status='present'"
    ).fetchall()
    updated = 0
    for r in rows:
        if r["hash"] is not None and r["hashed_mtime"] == r["mtime"]:
            continue  # хэш актуален — переиспользуем
        full = root / r["rel_path"]
        if not full.exists():
            continue
        digest = file_hash(full)
        conn.execute(
            "UPDATE files SET hash=?, hashed_mtime=? WHERE rel_path=?",
            (digest, r["mtime"], r["rel_path"]),
        )
        updated += 1
    conn.commit()
    return updated
