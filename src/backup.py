"""Сравнение исходной папки с резервной копией."""

from pathlib import Path

import scanner
import duplicates


def _index(root):
    """Строит словарь rel_path -> метаданные для папки."""
    return {f["rel_path"]: f for f in scanner.scan_folder(root)}


def compare(source, backup):
    """Сравнивает исходную папку с резервной копией.

    Возвращает словарь со списками относительных путей:
      missing — есть в источнике, но нет в копии;
      changed — есть в обоих, но содержимое отличается;
      extra   — лишние файлы, которых нет в источнике.
    """
    src = _index(source)
    bak = _index(backup)
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
