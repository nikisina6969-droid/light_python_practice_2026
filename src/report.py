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


def print_file_list(conn):
    """Печатает текущий индекс файлов из базы."""
    rows = conn.execute(
        "SELECT rel_path, size, file_type FROM files "
        "WHERE status = 'present' ORDER BY rel_path"
    ).fetchall()
    if not rows:
        print("Файлы не найдены.")
        return
    print(f"\nИндекс файлов ({len(rows)}):")
    print("-" * 60)
    for r in rows:
        print(f"{human_size(r['size']):>9}  {r['file_type']:<8}  {r['rel_path']}")
