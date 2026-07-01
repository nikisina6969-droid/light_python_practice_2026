"""Работа с базой SQLite: подключение и инициализация схемы.

Схема хранится в коде. База создаётся при запуске утилиты (полный вариант).
"""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("data") / "app.db"

# Индекс файлов и журнал запусков сканирования.
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

# Результаты сверки с резервной копией и история проверок.
BACKUP_SCHEMA = """
CREATE TABLE IF NOT EXISTS backup_checks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    source     TEXT    NOT NULL,
    backup     TEXT    NOT NULL,
    checked_at TEXT    NOT NULL,
    missing    INTEGER NOT NULL DEFAULT 0,
    changed    INTEGER NOT NULL DEFAULT 0,
    extra      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS backup_diffs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    check_id  INTEGER NOT NULL,
    rel_path  TEXT    NOT NULL,
    diff_type TEXT    NOT NULL,
    FOREIGN KEY (check_id) REFERENCES backup_checks(id)
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
    conn.executescript(BACKUP_SCHEMA)
    conn.commit()
