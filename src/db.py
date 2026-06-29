"""Работа с базой SQLite: подключение и инициализация схемы.

Схема хранится в коде. База создаётся при запуске утилиты (полный вариант).
"""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("data") / "app.db"

# Минимальная схема под индекс файлов.
# Поля hash/hashed_mtime заполняются на этапе поиска дубликатов.
SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    rel_path     TEXT    NOT NULL UNIQUE,
    size         INTEGER NOT NULL,
    mtime        REAL    NOT NULL,
    ext          TEXT,
    file_type    TEXT,
    hash         TEXT,
    hashed_mtime REAL,
    status       TEXT    NOT NULL DEFAULT 'present',
    scanned_at   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS scans (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    root       TEXT    NOT NULL,
    started_at TEXT    NOT NULL,
    files_seen INTEGER NOT NULL DEFAULT 0
);
"""


def connect(db_path=DEFAULT_DB_PATH):
    """Открывает соединение с базой, создавая папку при необходимости."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn):
    """Создаёт таблицы, если их ещё нет."""
    conn.executescript(SCHEMA)
    conn.commit()
