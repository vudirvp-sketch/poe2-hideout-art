---
Task ID: 1
Agent: main (super-z)
Task: v0.4.0 — Анализ 7 .hideout файлов (6 PoE1 + 1 PoE2).

Work Log:
- Прочитал 7 .hideout файлов. Нашёл что PoE использует duplicate keys.
- Написал parse_hideout.py — regex-парсер preserving duplicates.
- Создал PATTERNS.md с PoE1-паттернами (получился нерелевантным для PoE2).

Stage Summary:
- Главный артефакт: parse_hideout.py (используется до сих пор).
- Главный провал: PATTERNS.md был основан на PoE1 файлах и нерепрезентативном
  PoE2 functional hideout, дал неверные выводы про rotation quanta и 500-700
  placements.

---
Task ID: 2
Agent: main (super-z)
Task: v0.5.0 — попытка clean canvas для PoE2.

Work Log:
- Нашёл в `исходники/` 7 PoE2 image-hideout'ов + 7 JPG.
- Проанализировал: 8-19 artistic placements, r=0 почти всегда, вариативность через fv.
- Создал clean_v0.5.0.hideout — круг из Маракетских обломков + fill Береговой галькой.

Stage Summary:
- Файл clean_v0.5.0.hideout был неверным подходом: пользователь указал что
  `исходники/` — это каталог декора (показывает какой декор есть), а не
  референсы картин. И декор можно вращать (r не обязательно 0).
- Удалён в v0.6.0.

---
Task ID: 3
Agent: main (super-z)
Task: v0.6.0 — CLEANUP. Пользователь: "ты еблан? я тебе скидывал папку исходники чтобы продемонстрировать базовые декоративные элементы... Переписывай документацию для понимания и удаляй весь мусор и шлак с репозитория!"

Work Log:
- Скопировал репо в /home/z/my-project/repo_clean для чистки.
- Инвентаризация: в репо есть рабочая библиотека src/hideout_art/ + куча PoE1-мусора вокруг.
- УДАЛЕНО:
  * download/plot_*.png, rot_*.png, pertype_*.png (21 PoE1 visualization)
  * download/analysis_full.json, per_type_stats.json, spatial_stats.json (PoE1 анализы)
  * download/чистый холст*.hideout, *.png (старые v0.3.0/v0.4.0 попытки)
  * download/clean_v0.5.0.*, poe2_refs_analysis.json, poe2_overlay/ (v0.5.0 мусор)
  * AGENTS.md, CHANGELOG.md, CONTRIBUTING.md, INSTALL.md, SECURITY.md (15+14+3+5+1 KB лишнего)
  * PATTERNS.md (PoE1 based, заменён на DECO_CATALOG.md)
  * docs/img2hideout.md, docs/mosaic_recipe.md (PoE1 based)
  * examples/palette*.json (PoE1 based)
  * deliverable/ (старые попытки)
  * scripts/analyze_all.py, per_type_stats.py, per_type_grid.py, spatial_stats.py,
    plot_hideouts.py, draw_primitives.py, render_primitives_preview.py,
    sample_pixels.py, sample_all.py, scrape_hashes.py, bulk_preview.py (11 PoE1 scripts)
- ОСТАВЛЕНО:
  * src/hideout_art/ (библиотека без изменений)
  * scripts/parse_hideout.py, scripts/measure_decorations.py (полезные)
  * docs/format.md (спецификация, актуальна)
  * tests/ (тесты библиотеки)
  * исходники/ (каталог декора пользователя)
  * examples/README.md, pyproject.toml, LICENSE, .gitignore, .gitattributes, .github/
- СОЗДАНО:
  * README.md — короткий, понятный обзор проекта
  * DECO_CATALOG.md — каталог 27 декоров (hash + fv-диапазоны + RGB + размер + источник)
  * STATUS.md — v0.6.0, чистый, KI-12/13/14 актуальные, KI-22 superseded
  * worklog.md (этот файл)

Stage Summary:
- Репозиторий очищен от PoE1-мусора. Объём документации сокращён с ~50 KB до ~12 KB.
- Создан DECO_CATALOG.md — единый источник правды по доступному декору.
- Пользовательское понимание исправлено:
  * `исходники/` = каталог декора (не картины-референсы)
  * декор можно вращать (r поле поддерживает любые значения)
  * задача: img2hideout — превратить картинку в .hideout
- Рабочая библиотека src/hideout_art/ сохранена без изменений.
- Готов к тесту img2hideout на простом изображении (TODO-1 в STATUS.md).
