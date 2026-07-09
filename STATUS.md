# STATUS.md

## Текущее состояние

**v0.4.0 — ANALYSIS READY.** Готов корпус закономерностей по 7 .hideout файлам
(6 PoE1 + 1 PoE2). Документированы формат, паттерны размещения, роли doodad'ов,
ротация, канонический алгоритм img2hideout. Скрипты анализа работают, JSON-статы
и PNG-визуализации сохранены.

**Что изменилось по сравнению с предыдущей итерацией:**
- Прошлая итерация пыталась рисовать портреты наугад → получалась "срань".
- Эта итерация:停下来, проанализировали 7 готовых примеров, вычленили закономерности.
- Создан `PATTERNS.md` — канонический справочник.
- Парсер `scripts/parse_hideout.py` правильно обрабатывает duplicate keys (json.load теряет).

---

## Известные проблемы (Known Issues)

### KI-19 (NEW, blocker) — нет верификации в игре
**Симптом**: Все выводы в PATTERNS.md основаны на позициях/хэшах из .hideout файлов,
но **не на визуальной проверке в игре**. Какие реальные цвета/текстуры у декора —
неизвестно.
**Фикс**: пользователь должен прислать скриншоты PoE1 и PoE2 убежищ с этими doodad'ами.
**Блокирует**: построение "color palette" и успешный img2hideout.

### KI-20 (NEW) — только 1 PoE2 референс
**Симптом**: Все PoE2-специфичные выводы (доминанта 311.6°, 2-типовая палитра
大理石長凳+洞穴石化像) основаны на одном файле `poe2.hideout`.
**Фикс**: получить ещё 2-3 PoE2 image-hideout'а для перекрёстной проверки.
**Не блокирует**: img2hideout v1, но ограничивает точность.

### KI-21 (NEW) — variant (fv) mapping не задокументирован
**Симптом**: Значения `fv` 0..18 встречаются часто, 129..146 — с flip=1.
Какой число → какой визуальный вариант модели — неизвестно.
**Фикс**: инспектировать в игре каждый doodad с разными fv.
**Не блокирует**: img2hideout v1 (можно зафиксировать fv=0).

### KI-18 — superseded
Ранее: clean_composition ждёт visual-verify.
**Closed**: подход clean_composition из v0.3.0 был неверным — нужно следовать
PATTERNS.md §5 каноническому алгоритму, а не плодить примитивы.

### KI-17 — superseded
Ранее: откат к single-decoration примитивам.
**Closed**: уточнено — нужно использовать 4-рольную палитру (FILL+STROKE+OUTLINE+ACCENT),
не 1 decoration.

### KI-16 — superseded
**Closed**: устарел.

---

## TODO — приоритеты следующей итерации

1. **Дождаться скриншотов от пользователя** (KI-19) — без этого генерация картинок вслепую.
   - Что прислать: скриншоты PoE1 hideout с топ-doodad'ами (火山卵石, 大理石板, 營地地毯, 飄雪, 寶石袋, 冰湖, 藍色光束)
   - Что прислать: скриншот PoE2 hideout с大理石長凳 и 洞穴石化像
   - Цель: построить `COLOR_PALETTE.md` (hash → real-game color/texture).

2. **Реализовать img2hideout v1** по `PATTERNS.md §5`:
   - Input: PNG/JPG
   - Downsample → integer grid
   - Role classification (FILL/STROKE/OUTLINE/ACCENT)
   - Doodad mapping per role (PoE1 или PoE2 mode)
   - Rotation assignment per zone
   - Output: .hideout в new JSON format с duplicate keys
   - Скрипт: `scripts/img2hideout.py`

3. **Verify PoE2 hypothesis** (KI-20) — попросить у пользователя ещё PoE2 hideouts.

4. **Variant mapping** (KI-21) — после получения скриншотов.

---

## Что НЕ сделано (намеренно, "лучше недоделать")

- `scripts/img2hideout.py` — нет, потому что без KI-19 (color palette) результат
  будет вслепую и снова получится "срань".
- Portrait comp из чистых примитивов — отложен, пока не верифицированы паттерны
  реальными скриншотами.
- Multi-pass img2hideout (outline + fill) — отложен до v1 single-pass.

---

## Файловая структура проекта

```
PATTERNS.md              # Канонический справочник закономерностей
STATUS.md                # Этот файл
worklog.md               # Журнал работы (append-only)
scripts/
  parse_hideout.py       # Duplicate-preserving парсер .hideout (regex)
  analyze_all.py         # Базовый анализ всех файлов (счёт, bbox, top-types)
  spatial_stats.py       # NN distances, grid detection, rotation Moran's I
  per_type_stats.py      # Per-doodad role classification (FILL/STROKE/OUTLINE/ACCENT)
  plot_hideouts.py       # Type-color + rotation heatmap PNG для каждого файла
  per_type_grid.py       # Per-type breakdown PNG (red=этот тип, grey=остальные)
download/
  analysis_full.json     # Полный статистический dump
  spatial_stats.json     # NN/grid/rotation цифры
  per_type_stats.json    # Per-doodad role classification
  plot_*.png             # 7 type-color scatter plots
  rot_*.png              # 7 rotation heatmaps
  pertype_*.png          # 7 per-type breakdowns
upload/                  # Оригинальные .hideout файлы от пользователя
```
