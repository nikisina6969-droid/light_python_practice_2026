"""Консольный индексатор папок. Точка входа.

Этап 3: сканирование + подсчёт хэшей и поиск дубликатов.
"""

import argparse
from pathlib import Path

import db
import scanner
import report
import duplicates


def build_parser():
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Индексатор папок (полный вариант): "
                    "сканирование, дубликаты, сверка резервной копии.",
    )
    parser.add_argument("path", help="Путь к папке для индексации")
    parser.add_argument("--db", default=str(db.DEFAULT_DB_PATH),
                        help="Путь к файлу базы SQLite (по умолчанию data/app.db)")
    parser.add_argument("--filter-ext", metavar="EXT",
                        help="Показать только файлы с расширением, напр. .txt")
    parser.add_argument("--filter-name", metavar="SUB",
                        help="Показать только файлы с подстрокой в пути")
    parser.add_argument("--duplicates", action="store_true",
                        help="Посчитать хэши и показать группы дубликатов")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    target = Path(args.path)
    if not target.is_dir():
        print(f"Ошибка: папка не найдена: {target}")
        return 1

    conn = db.connect(args.db)
    db.init_db(conn)

    # Индекс всегда обновляем, чтобы он отражал текущее состояние папки.
    files = scanner.scan_folder(target)
    scanner.save_index(conn, files, target)

    if args.duplicates:
        duplicates.update_hashes(conn, target)
        groups = duplicates.find_duplicates(conn)
        report.print_duplicates(groups)
    else:
        report.print_file_list(conn, args.filter_ext, args.filter_name)

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
