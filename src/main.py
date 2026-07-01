"""Консольный индексатор папок. Точка входа.

Полный вариант: сканирование, поиск дубликатов, сверка резервной копии.
"""

import argparse
from pathlib import Path

import db
import scanner
import report
import duplicates
import backup


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
    parser.add_argument("--backup", metavar="BACKUP_PATH",
                        help="Сравнить папку с резервной копией по этому пути")
    parser.add_argument("--history", action="store_true",
                        help="Показать историю проверок резервной копии")
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

    if args.backup:
        bpath = Path(args.backup)
        if not bpath.is_dir():
            print(f"Ошибка: папка резервной копии не найдена: {bpath}")
            conn.close()
            return 1
        diff = backup.compare(target, bpath)
        backup.save_check(conn, target.resolve(), bpath.resolve(), diff)
        report.print_backup(diff)
    elif args.duplicates:
        duplicates.update_hashes(conn, target)
        report.print_duplicates(duplicates.find_duplicates(conn))
    else:
        report.print_file_list(conn, args.filter_ext, args.filter_name)
        report.print_missing(conn)

    if args.history:
        report.print_history(conn)

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
