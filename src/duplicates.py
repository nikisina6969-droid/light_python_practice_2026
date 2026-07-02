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


def find_duplicates(conn):
    """Возвращает группы файлов с одинаковым хэшем (2+ файла).

    Группировка выполняется одним SQL-запросом: GROUP BY по хэшу и HAVING
    COUNT(*) > 1 оставляет только повторяющиеся, а group_concat собирает пути
    группы в одну строку (разделитель — перевод строки). Формат результата:
    список кортежей (hash, size, [rel_path, ...]).
    """
    rows = conn.execute(
        """
        SELECT hash,
               size,
               COUNT(*) AS cnt,
               group_concat(rel_path, char(10)) AS paths
        FROM (
            SELECT hash, size, rel_path
            FROM files
            WHERE status = 'present' AND hash IS NOT NULL
            ORDER BY rel_path
        )
        GROUP BY hash
        HAVING cnt > 1
        ORDER BY hash
        """
    ).fetchall()
    return [(r["hash"], r["size"], r["paths"].split("\n")) for r in rows]
