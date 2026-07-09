# STATUS.md

Текущее состояние проекта `poe2-hideout-art`. Короткая живая памятка для
агента/человека: что работает, что сломано, что делать дальше. Длинную
историю изменений не ведём — для этого есть `CHANGELOG.md`.

## Что работает (проверено 2026-07-10, версия 0.2.8)

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
- **Drawing primitives (0.2.8)** — модуль `src/hideout_art/primitives.py`
  + `scripts/draw_primitives.py`. **9 базовых фигур**:
  - **Core (0.2.7)**: `line`, `polyline`, `hollow_circle`, `filled_circle`,
    `s_snake`, `thick_line_with_contours`, + курируемая `center_composition`.
  - **Mosaic/bas-relief (0.2.8, NEW)**: `arc`, `rectangle`, `polygon`,
    `grid` — для арок, рамок, n-угольников, мозаичных сеток.
- **Визуальная проверка в игре (0.2.7)** — 3/5 фигур узнаваемы. KI-14/15
  зафиксены в 0.2.8 — ожидается повторная проверка (5/5) от пользователя.
- Тесты: **332 pass, 1 skipped** (22 новых в `tests/test_primitives.py`
  для arc/rectangle/polygon/grid + 2 KI-14/15 regression tests).

## Известные проблемы (Known Issues)

Все ранее задокументированные KI-1..KI-12 закрыты или low-priority.
Активные:

| KI  | Статус        | Приоритет | Что                                                                |
|-----|---------------|-----------|--------------------------------------------------------------------|
| KI-2 | wontfix 0.2.7 | low       | Skin-роль. Решено: точное попадание в RGB не нужно, главное — различимость. |
| KI-10 | open 0.2.3   | low       | Каталог измеряет placement footprint, не sprite bounds.            |
| KI-12 | wontfix 0.2.7 | low      | Marble-серия pixel-sampling даёт brown вместо gray.                |
| KI-13 | closed 0.2.8  | —        | Drawing primitives: 3/5 узнаваемы в 0.2.7. KI-14/15 фикс в 0.2.8 закрыл пробел. Ожидает повторной проверки. |
| KI-14 | fixed 0.2.8   | —        | S-snake: заменён декоратор Sand Tussock → Maraket Rubble (плотнее + контрастнее). |
| KI-15 | fixed 0.2.8   | —        | Thick_line: thickness 14 → 28, fill Coastal Pebble → Long Grass (2 ряда заливки). |

### KI-14 (fixed 0.2.8) — S-snake плохо различима

В 0.2.7 S-snake использовал `Sand Tussock` (min_spacing=17.1, тёмная
олива) при height=60, width=25 — размещения расположены слишком редко,
форма не читалась.

**Фикс (0.2.8):** `s_snake_decoration` в `center_composition` сменён на
`Maraket Rubble` (min_spacing=13.6 — на 21% плотнее placement,
нейтрально-коричневый, выше контраст на tan-полу Canal Hideout). S-snake
теперь даёт 6 точек (было 5) при том же height=60.

### KI-15 (fixed 0.2.8) — Thick_line stadium не видна

В 0.2.7 thick_line использовал `thickness=14` и `Coastal Pebble` fill
(min_spacing=29.7). Полоса 14 wu давала ≤1 ряд fill-точек — контур
сливался с фоном.

**Фикс (0.2.8):** `thickness` увеличен до 28 (2× min_spacing of Long
Grass), fill сменён на `Long Grass` (min_spacing=13.3, видимость
подтверждена KI-13 vertical lines). При length=50, sp=13.3 теперь:
4 ряда × 2 fill-ячейки = 8 fill-точек (часть фильтруется внутри caps),
+ 6 long-side outline + 14 cap outline = 18 outline. Всего ~26 точек.
Outline `Small Coastal Stone` сохранён (тёмный, контрастирует с Long
Grass fill).

### KI-10 (open 0.2.3, low) — placement vs sprite bounds

`DECORATION_FOOTPRINT_CATALOG` измеряет **placement footprint** (upper
bound на основе min pairwise distance), не реальные sprite bounds. Для
step-калибровки `img2hideout` достаточно; для визуального перекрытия
нужны внутриигровые замеры sprite. **Низкий приоритет.**

### KI-2 (wontfix 0.2.7) — skin-роль в палитре 2B

Решено: точное попадание в RGB (228,200,178) не нужно. Главное —
различимость фигур на полу. Если понадобится тёплый accent — использовать
`Maraket Treasures` (gold) или `Maraket Samovar` (copper).

### KI-12 (wontfix 0.2.7) — Marble-серия pixel-sampling

Pixel sampling показал brown (76-110) вместо ожидаемого light gray
(210-230) для Marble Bench/Walls/Fountain. Причина: sampling window
попадает на тень под объектом. **Не критично** — при переходе на другие
убежища проблема уйдёт.

## Что улучшать дальше (приоритеты следующей итерации)

1. **Повторная визуальная проверка 0.2.8.** Пользователь импортирует
   `download/чистый холст с примитивами.hideout` в PoE2, делает
   скриншоты. Ожидаем 5/5 узнаваемых. Если нет — завести KI-16 с
   конкретной фигурой.
2. **Multi-pass img2hideout: outline + fill.** Реализуется в
   `img2hideout.py` через `outline_color` + двухпроходной рендер. Готовый
   паттерн — `thick_line_with_contours` в `primitives.py`.
3. **Расширить `center_composition` новыми примитивами 0.2.8.** Сейчас
   композиция использует только 5 core-фигур. Добавить демонстрацию
   `polygon` (hexagon) + `arc` (semicircle) + `grid` (3×3 mosaic tile)
   в свободной зоне холста.
4. **Sprite bounds (KI-10).** Расширить `DECORATION_FOOTPRINT_CATALOG`
   полем `sprite_bounds_wu` отдельно от placement footprint.
5. **Drawing primitives v3.** После визуальной проверки 0.2.8: добавить
   `bezier_curve`, `text` (через bitmap font), `concentric_rings`.
6. **Поддержка нескольких убежищ.** Сейчас `NAMED_BOUNDS` содержит только
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
   на полу.
