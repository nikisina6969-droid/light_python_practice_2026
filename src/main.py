"""Консольный индексатор папок. Точка входа.

Этап 1 (каркас): принимает путь к папке и инициализирует базу SQLite.
"""

import argparse
from pathlib import Path

import db


def build_parser():
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Индексатор папок (полный вариант): "
                    "сканирование, дубликаты, сверка резервной копии.",
    )
    parser.add_argument("path", help="Путь к папке для индексации")
    parser.add_argument(
        "--db",
        default=str(db.DEFAULT_DB_PATH),
        help="Путь к файлу базы SQLite (по умолчанию data/app.db)",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    target = Path(args.path)
    if not target.is_dir():
        print(f"Ошибка: папка не найдена: {target}")
        return 1

    conn = db.connect(args.db)
    db.init_db(conn)
    conn.close()

    print(f"База инициализирована: {args.db}")
    print(f"Папка для индексации:  {target.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
