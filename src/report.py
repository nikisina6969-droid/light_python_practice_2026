"""Форматированный вывод отчётов в консоль."""


def human_size(n):
    """Размер в человекочитаемом виде."""
    size = float(n)
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if size < 1024 or unit == "ГБ":
            if unit == "Б":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024


def print_file_list(conn, ext_filter=None, name_filter=None):
    """Печатает индекс файлов из базы.

    Фильтры (необязательные) ограничивают только вывод, не трогая индекс:
      ext_filter  — показать файлы с расширением, напр. ".txt";
      name_filter — показать файлы, в относительном пути которых есть подстрока.
    """
    query = "SELECT rel_path, size, file_type FROM files WHERE status = 'present'"
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
