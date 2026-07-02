"""Сравнение исходной папки с резервной копией."""

from datetime import datetime, timezone
from pathlib import Path

import scanner
import duplicates


def _index(root):
    """Строит словарь rel_path -> метаданные для папки."""
    return {f["rel_path"]: f for f in scanner.scan_folder(root)}


def _match(meta, rel, ext_filter, name_filter):
    """Проверяет, подходит ли файл под фильтры (расширение / подстрока имени)."""
    if ext_filter:
        ext = ext_filter.lower()
        if not ext.startswith("."):
            ext = "." + ext
        if meta["ext"] != ext:
            return False
    if name_filter and name_filter.lower() not in rel.lower():
        return False
    return True


def compare(source, backup, ext_filter=None, name_filter=None):
    """Сравнивает исходную папку с резервной копией.

    Если заданы фильтры, в сравнение попадают только подходящие файлы.
    Возвращает словарь со списками относительных путей:
      missing — есть в источнике, но нет в копии;
      changed — есть в обоих, но содержимое отличается;
      extra   — лишние файлы, которых нет в источнике.
    """
    src = {rel: m for rel, m in _index(source).items()
           if _match(m, rel, ext_filter, name_filter)}
    bak = {rel: m for rel, m in _index(backup).items()
           if _match(m, rel, ext_filter, name_filter)}
    src_paths, bak_paths = set(src), set(bak)

    missing = sorted(src_paths - bak_paths)
    extra = sorted(bak_paths - src_paths)
    changed = []
    for rel in sorted(src_paths & bak_paths):
        # Сначала быстрый признак — размер, при совпадении сверяем по хэшу.
        if src[rel]["size"] != bak[rel]["size"]:
            changed.append(rel)
        elif duplicates.file_hash(Path(source) / rel) != duplicates.file_hash(Path(backup) / rel):
            changed.append(rel)
    return {"missing": missing, "changed": changed, "extra": extra}


def save_check(conn, source, backup, diff):
    """Сохраняет результат проверки и её детали в SQLite (история запусков)."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cur = conn.execute(
        "INSERT INTO backup_checks (source, backup, checked_at, missing, changed, extra) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (str(source), str(backup), now,
         len(diff["missing"]), len(diff["changed"]), len(diff["extra"])),
    )
    check_id = cur.lastrowid
    for diff_type in ("missing", "changed", "extra"):
        for rel in diff[diff_type]:
            conn.execute(
                "INSERT INTO backup_diffs (check_id, rel_path, diff_type) VALUES (?, ?, ?)",
                (check_id, rel, diff_type),
            )
    conn.commit()
    return check_id
