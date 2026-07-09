# STATUS.md

Текущее состояние проекта `poe2-hideout-art`. Короткая живая памятка для
агента/человека: что работает, что сломано, что делать дальше. Длинную
историю изменений не ведём — для этого есть `CHANGELOG.md`.

## Что работает (проверено 2026-07-09, версия 0.2.7)

- Парсер `.hideout` (толерантный, регэксп, сохраняет дубликаты ключей).
- Врайтер (байт-совместимый, дубликаты ключей сохраняет).
- Геометрические трансформации: `shift`, `rotate`, `mirror_x`, `mirror_y`,
  `recombine`.
- Превью в PNG (matplotlib, по одной точке на размещение).
- Конвейер `img2hideout` (alpha-канал, 3 цветовых метрики, Floyd-Steinberg
  dithering, jitter, `step`/`tile_size`, `bounds`, `resample`, `--preview`).
- CLI: `inspect`, `layers`, `stats`, `preview`, `shift`, `transfer`,
  `img2hideout`.
- Каталог хешей: **47 известных декораций** (11 functional + 8 NPC +
  28 art). `DECORATION_FOOTPRINT_CATALOG` покрывает все 28 art-декораций.
- Pixel-sampling (`scripts/sample_pixels.py`) — ground-truth RGB для 25
  из 28 art-декораций.
- **Drawing primitives (0.2.7)** — модуль `src/hideout_art/primitives.py`
  + `scripts/draw_primitives.py`. Рисует 5 базовых фигур декорациями
  прямо в world-координатах: `line`, `hollow_circle`, `filled_circle`,
  `s_snake`, `thick_line_with_contours`, + курируемая `center_composition`.
- **Визуальная проверка в игре (0.2.7, NEW)** — пользователь импортировал
  `чистый холст с примитивами.hideout` в PoE2, сделал 2 скриншота.
  Результат: 3/5 фигур узнаваемы, 2/5 нужно доработать (см. KI-13 ниже).
- Тесты: **310 pass, 1 skipped** (37 новых в `tests/test_primitives.py`).

## Известные проблемы (Known Issues)

Все ранее задокументированные KI-1..KI-11 закрыты или low-priority. Активные:

| KI  | Статус        | Приоритет | Что                                                                |
|-----|---------------|-----------|--------------------------------------------------------------------|
| KI-2 | wontfix 0.2.7 | low       | Skin-роль. Решено: точное попадание в RGB не нужно, главное — различимость. Текущая палитра достаточна. |
| KI-10 | open 0.2.3   | low       | Каталог измеряет placement footprint, не sprite bounds.            |
| KI-12 | wontfix 0.2.7 | low      | Marble-серия pixel-sampling даёт brown вместо gray. Не критично — переход на другие убежища решит проблему. |
| KI-13 | partial 0.2.7 | **high** | Drawing primitives: 3/5 фигур узнаваемы в игре, 2/5 нужно доработать (см. ниже). |
| KI-14 | new 0.2.7    | **high** | S-snake из Sand Tussock плохо различима — нужен более контрастный декоратор. |
| KI-15 | new 0.2.7    | **high** | Thick_line при thickness=14 не видна — нужно увеличить thickness до 28-30 + использовать Long Grass для fill. |

### KI-13 (partial 0.2.7) — Drawing primitives: 3/5 узнаваемы

Визуальная проверка в игре (2 скриншота от пользователя) показала:

**Хорошо видны (3/5):**
- ✅ **3 вертикальные линии (Long Grass)** — хорошо видны, форма узнаваема.
  Опровергает опасение KI-13(b) о Long Grass visibility.
- ✅ **Полый круг (Maraket Rubble)** — виден, немного фрагментирован, но
  узнаваем.
- ✅ **Заполненный круг (Coastal Pebble)** — виден, узнаваем.

**Плохо видны (2/5):**
- ❌ **S-snake (Sand Tussock)** — частично видна, форма НЕ узнаваема.
  Sand Tussock слишком мелкий/неплотный для кривой. См. KI-14.
- ❌ **Thick line stadium (Small Coastal Stone outline + Coastal Pebble fill)**
  — частично видна, форма НЕ узнаваема. Thickness=14 слишком мала при
  spacing декораций. См. KI-15.

**Опровержения:**
- (a) Sprite overlap при tight spacing — НЕ подтверждено. Spacing из
  каталога работает корректно, перекрытий нет.
- (b) Long Grass visibility — НЕ подтверждено. Long Grass отлично виден
  на полу Canal Hideout.

### KI-14 (new 0.2.7) — S-snake плохо различима

Sand Tussock — мелкая тёмная трава, при S-образной кривой (height=60,
width=25) размещения расположены слишком редко, чтобы прочитать форму.

**Что закроет KI-14:**
- Заменить декоратор S-snake на более контрастный/плотный:
  `Maraket Rubble` (sp=13.6, reddish-brown) или
  `Small Coastal Stone` (sp=15, dark).
- Либо увеличить amplitude (width=40-50) и уменьшить spacing до 10-12.
- Либо использовать `polyline` с большей плотностью точек.

### KI-15 (new 0.2.7) — Thick_line stadium не видна

При `thickness=14` и fill декорации `Coastal Pebble` (min_spacing=15.5)
заливка содержит ≤1 ряд точек — контур не выделяется на фоне заливки.
Outline из `Small Coastal Stone` (sp=15) тоже сливается с фоном пола.

**Что закроет KI-15:**
- Увеличить `thickness` до 28-30 (2× spacing fill-декорации).
- Использовать `Long Grass` (sp=13.3) для fill — он контрастно выделяется
  на полу (см. KI-13 vertical lines).
- Для outline оставить `Small Coastal Stone` или `Maraket Rubble`.

### KI-10 (open 0.2.3) — placement vs sprite bounds

`DECORATION_FOOTPRINT_CATALOG` измеряет **placement footprint** (upper
bound на основе min pairwise distance), не реальные sprite bounds. Видимая
крона дерева выходит за placement-тайл. Для step-калибровки `img2hideout`
достаточно; для визуального перекрытия нужны внутриигровые замеры sprite.
**Низкий приоритет** — текущая работа не требует точных sprite bounds.

### KI-2 (wontfix 0.2.7) — skin-роль в палитре 2B

Решено: точное попадание в RGB (228,200,178) не нужно. Главное —
различимость фигур на полу. Текущие 5 из 6 ролей в `palette_2b.json`
достаточны для portrait-режима. Если понадобится тёплый accent —
использовать `Maraket Treasures` (gold) или `Maraket Samovar` (copper).

### KI-12 (wontfix 0.2.7) — Marble-серия pixel-sampling

Pixel sampling показал brown (76-110) вместо ожидаемого light gray (210-230)
для Marble Bench/Walls/Fountain. Только Marble Table даёт bright cream.
Причина: sampling window попадает на тень под объектом. **Не критично** —
при переходе на другие убежища (с чистыми Marble декорациями) проблема
уйдёт. Manual calibration (`scripts/calibrations/<stem>.json` с 3+ anchors
+ `--sample-offset-y-wu`) остаётся как fallback, но не в приоритете.

## Что улучшать дальше (приоритеты следующей итерации)

1. **Fix KI-14 + KI-15 (главный приоритет).** Обновить `center_composition`
   в `primitives.py`:
   - S-snake: декоратор `Maraket Rubble` вместо `Sand Tussock`.
   - Thick line: `thickness=28`, fill `Long Grass`, outline `Small Coastal
     Stone` (или `Maraket Rubble`).
   - Перегенерировать `чистый холст с примитивами.hideout`.
   - Повторить визуальную проверку (5/5 фигур должны быть узнаваемы).
2. **Multi-pass img2hideout: outline + fill.** Реализуется в `img2hideout.py`
   через `outline_color` + двухпроходной рендер. Готовый паттерн —
   `thick_line_with_contours` в `primitives.py`.
3. **Sprite bounds (KI-10).** Расширить `DECORATION_FOOTPRINT_CATALOG`
   полем `sprite_bounds_wu` отдельно от placement footprint.
4. **Drawing primitives v2.** После KI-14/15: добавить `arc`, `bezier_curve`,
   `polygon`, `text` (через bitmap font).
5. **Поддержка нескольких убежищ.** Сейчас `NAMED_BOUNDS` содержит только
   `canal`. Добавлять новые по мере появления экспортов.

## Базовые принципы при правках

1. **Сначала в STATUS.md, потом фикс.** Новый баг → новый KI-N → потом код.
2. **Никогда не ломать существующие тесты.** Все новые опции — opt-in.
3. **Никогда не выдумывать хеши.** Нет в `KNOWN_HASHES` → помечаем unknown.
4. **RGB-значения — с указанием источника и даты.** `VLM <version>, <date>`
   или `PIXEL <version>, <date>`. При конфликте доверять PIXEL.
5. **Документация короткая.** Этот файл — не больше 130 строк.
6. **Каталог размеров — sync с исходниками.** При добавлении размещений
   в `исходники/` перезапускать `scripts/measure_decorations.py` и
   обновлять `DECORATION_FOOTPRINT_CATALOG`.
7. **Drawing primitives — только ART_TYPES.** Никогда не использовать
   functional-объекты в примитивах (см. `safe_spacing` в `primitives.py`).
8. **Точное попадание в RGB — НЕ нужно.** Главное — различимость фигур
   на полу. Не тратить время на pixel-perfect color matching.
