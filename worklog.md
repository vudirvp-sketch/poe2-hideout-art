---
Task ID: 1
Agent: main (super-z)
Task: Анализ 7 .hideout файлов (6 PoE1 + 1 PoE2) — вычленить паттерны, алгоритмы, закономерности композиции изображений. Зафиксировать в документации. Пользователь недоволен предыдущими итерациями ("откровенная срань") — нужен анализ готовых примеров, а не слепая генерация.

Work Log:
- Прочитал 7 .hideout файлов: 6 PoE1 (Cat windowsill, CatGirl, Nayuta, Rent girlfriend, Pikachu, cross ones leg) + 1 PoE2 (poe2.hideout).
- Обнаружил что PoE .hideout JSON использует duplicate keys для нескольких placements одного doodad'а. json.load() теряет эти дубликаты → счёт 21 вместо 450.
- Написал scripts/parse_hideout.py: regex-парсер preserving duplicates, поддерживает оба формата (new JSON + old text), UTF-8 + UTF-16.
- Написал scripts/analyze_all.py: счёт, bbox, top-types, r/fv distributions для всех 7 файлов.
- Написал scripts/spatial_stats.py: nearest-neighbor distances, grid detection, rotation angle bins, Moran's I proxy для spatial correlation ротации.
- Написал scripts/per_type_stats.py: per-doodad role classification (FILL/STROKE/OUTLINE/ACCENT/SINGLETON) по NN-same distance и доле от общего числа.
- Написал scripts/plot_hideouts.py: type-color scatter + rotation heatmap для каждого файла (14 PNG).
- Написал scripts/per_type_grid.py: per-type breakdown 3x3 grid для каждого файла (7 PNG).
- Запустил VLM-анализ (через subagent) всех PNG для подтверждения количественных выводов визуально.
- Синтезировал все данные в PATTERNS.md: формат файла, структура изображения, ротация, роли doodad'ов, канонический алгоритм img2hideout, анти-паттерны.
- Создал STATUS.md (v0.4.0) с новыми KI-19/20/21, закрытыми KI-16/17/18, приоритетами следующей итерации.

Stage Summary:
- Главные выводы:
  1. poe2.hideout — это рисунок (450 placements), не функциональное убежище. Раньше я думал наоборот.
  2. Координаты integer grid, hand-placed (НЕ регулярная сетка). NN median = √2 ≈ 1.414.
  3. Каждый рисунок: 1 FILL тип (30-65%) + 1-3 STROKE (10-25%) + 5-15 OUTLINE/ACCENT. PoE1 FILL = 火山卵石, PoE2 FILL = 洞穴石化像.
  4. Rotation квантуется к 11.25°/22.5°, 6/7 файлов доминируют в back-quadrant (270-360°). 315° — универсальный "второй угол".
  5. Rotation пространственно коррелирована (Moran's I 0.07-0.30, всегда > 0).
  6. Anti-pattern: НЕ использовать json.load() для готовых .hideout — теряет duplicate keys.
- Артефакты: PATTERNS.md, STATUS.md, 6 scripts в /scripts, 21 PNG + 3 JSON в /download.
- Пользователь ждёт: (1) архив с изменениями, (2) git-команды, (3) точку остановки.
- Блокеры для следующей итерации: KI-19 (нужны скриншоты из игры), KI-20 (нужны ещё PoE2 референсы).
