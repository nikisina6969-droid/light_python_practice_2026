"""Форматированный вывод отчётов в консоль."""


def human_size(n):
    size = float(n)
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if size < 1024 or unit == "ГБ":
            if unit == "Б":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024


def print_file_list(conn, ext_filter=None, name_filter=None):
    query = "SELECT rel_path, size, file_type FROM files WHERE status='present'"
    params = []
    if ext_filter:
        ext = ext_filter.lower()
        if not ext.startswith("."):
            ext = "." + ext
        query += " AND ext = ?"
        params.append(ext)
    if name_filter:
        query += " AND lower(rel_path) LIKE ?"
        params.append(f"%{name_filter.lower()}%")
    query += " ORDER BY rel_path"
    rows = conn.execute(query, params).fetchall()
    if not rows:
        print("Файлы не найдены.")
        return
    print(f"\nИндекс файлов ({len(rows)}):")
    print("-" * 60)
    for r in rows:
        print(f"{human_size(r['size']):>9}  {r['file_type']:<8}  {r['rel_path']}")


def print_missing(conn):
    """Печатает файлы, которые были в индексе, но исчезли из папки."""
    rows = conn.execute(
        "SELECT rel_path FROM files WHERE status='missing' ORDER BY rel_path"
    ).fetchall()
    if not rows:
        return
    print(f"\nУдалены (отсутствуют с прошлого скана): {len(rows)}")
    print("-" * 60)
    for r in rows:
        print(f"   - {r['rel_path']}")


def print_duplicates(groups):
    if not groups:
        print("\nДубликаты не найдены.")
        return
    total = sum(len(paths) for _h, _s, paths in groups)
    print(f"\nГрупп дубликатов: {len(groups)} (всего файлов: {total})")
    print("=" * 60)
    for i, (h, size, paths) in enumerate(groups, 1):
        print(f"\nГруппа {i} | {len(paths)} файла(ов) | {human_size(size)} | {h[:12]}…")
        for rel in paths:
            print(f"   - {rel}")


def _section(title, items):
    print(f"\n{title}: {len(items)}")
    for rel in items:
        print(f"   - {rel}")


def print_backup(diff):
    """Печатает итог сверки с резервной копией."""
    print("\nСверка резервной копии")
    print("=" * 60)
    _section("Отсутствуют в копии", diff["missing"])
    _section("Изменены", diff["changed"])
    _section("Лишние в копии", diff["extra"])
    if not any(diff.values()):
        print("\nРазличий не найдено — копия актуальна.")


def print_history(conn, limit=10):
    """Печатает историю последних проверок резервной копии."""
    rows = conn.execute(
        "SELECT checked_at, missing, changed, extra FROM backup_checks "
        "ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    if not rows:
        print("\nИстория проверок пуста.")
        return
    print(f"\nИстория проверок (последние {len(rows)}):")
    print("-" * 60)
    for r in rows:
        print(f"{r['checked_at']}   отсутствуют: {r['missing']}   "
              f"изменены: {r['changed']}   лишние: {r['extra']}")
