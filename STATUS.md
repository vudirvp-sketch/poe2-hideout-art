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
- Конвейер `img2hideout`:
  - базовый режим совместим с 0.1.0 побайтово;
  - alpha-канал PNG, 3 цветовых метрики, Floyd-Steinberg dithering;
  - jitter, `step`/`tile_size`, `bounds` (включая `--bounds canal`),
  - `resample`, `--preview` в CLI.
- CLI: `inspect`, `layers`, `stats`, `preview`, `shift`, `transfer`,
  `img2hideout`.
- Каталог хешей: **47 известных декораций** (11 функциональных + 8 NPC +
  4 исходных art + 5 Maraket/Coastal Pebble + 18 Canal из «исходники/» +
  1 Seaweed).
- Геометрия Canal Hideout: `CANAL_HIDEOUT_HASH = 60415`,
  `CANAL_HIDEOUT_BOUNDS = (700, 540, 860, 775)`.
- Каталог размеров декораций `DECORATION_FOOTPRINT_CATALOG` покрывает все
  28 art-декораций.
- Pixel-sampling: `scripts/sample_pixels.py` + `scripts/sample_all.json`
  (закрывает KI-11). Ground-truth RGB для 25 из 28 art-декораций.
- **Drawing primitives (0.2.7, НОВОЕ):** модуль `src/hideout_art/primitives.py`
  + скрипт `scripts/draw_primitives.py`. Рисует 5 базовых фигур
  декорациями прямо в world-координатах:
  - `line` — прямая линия между двумя точками;
  - `hollow_circle` — контур круга;
  - `filled_circle` — круг с заливкой (концентрические кольца);
  - `s_snake` — S-образная синусоида (вертикальная, один период);
  - `thick_line_with_contours` — «стадион» с контуром + заливкой.
  - `center_composition` — курируемая композиция из всех 5 фигур.
  Все примитивы соблюдают `DECORATION_FOOTPRINT_CATALOG.min_spacing_wu`,
  используют только `ART_TYPES`, не мутируют входной Hideout. Применено к
  пользовательскому `чистый холст.hideout` → 18 functional + 52 art = 70
  placements, round-trip OK.
- Тесты: **310 pass, 1 skipped** (37 новых в `tests/test_primitives.py`).

## Известные проблемы (Known Issues)

Все ранее задокументированные KI-1..KI-11 закрыты. Активные:

| KI  | Статус      | Что                                                |
|-----|-------------|----------------------------------------------------|
| KI-2 | partial 0.2.6 | 5/6 TODO закрыты. Остался `skin` — Sand Tussock подтверждён pixel-sampling как тёмный olive-tan (112,99,79), НЕ skin tone. Нужна новая peach/tan декорация. |
| KI-10 | new 0.2.3 | Каталог измеряет placement footprint, не sprite bounds. |
| KI-12 | new 0.2.6 | Marble-серия: pixel-sampled RGB (76-196 brown range) радикально отличается от VLM-оценок (210-230 light gray). Только Marble Table placement 1 даёт bright cream (237,208,169). Нужна manual калибровка или больший sampling radius для Marble-декораций. |
| KI-13 | new 0.2.7 | Drawing primitives готовы, но НЕ проверены в игре. Известные подзадачи: (a) sprite overlap при tight spacing может скрывать фигуры; (b) Long Grass имеет alpha-подобную траву — может быть плохо видна; (c) толщина thick_line ограничена min_spacing декорации fill. |

### KI-2 (обновлено 0.2.6) — холодная палитра 2B

| Роль | Декорация | RGB | Источник |
|------|-----------|-----|----------|
| white | Marble Fountain | (110,103,76) brown | PIXEL 0.2.6 — НЕ белый, Marble-серия проблемна (KI-12) |
| silver | Marble Table | (196,170,136) cream | PIXEL 0.2.6 — ближе к cream, не silver |
| gray | Marble Bench | (79,64,45) brown | PIXEL 0.2.6 — НЕ gray |
| gray alt | Marble Walls | (76,68,52) brown | PIXEL 0.2.6 — НЕ gray |
| black | Small Coastal Stone | (81,80,60) dark | PIXEL 0.2.6, подтверждает VLM 0.2.5 (85,75,70) |
| red | Maraket Rubble | (125,112,87) brown | PIXEL 0.2.6 — НЕ reddish (VLM 0.2.5 (153,78,68) был шумным) |
| skin | TODO_SKIN_DECORATION | (228,200,178) | НЕ найдено — Sand Tussock (112,99,79) слишком тёмный olive-tan |

**Что закроет KI-2 полностью:** новая peach/tan декорация из другого
убежища. Текущие 28 art-декораций не содержат подходящего peach/tan
цвета.

### KI-10 (0.2.3) — placement vs sprite bounds

`DECORATION_FOOTPRINT_CATALOG` измеряет **placement footprint** (upper
bound на основе min pairwise distance), не реальные sprite bounds. Видимая
крона дерева выходит за placement-тайл. Все наблюдения — при `r=0`. Для
step-калибровки `img2hideout` placement footprint достаточен; для
визуального перекрытия нужны внутриигровые замеры sprite.

### KI-12 (0.2.6) — Marble-серия pixel-sampling

Pixel sampling показал, что Marble Bench/Walls/Fountain все дают тёмные
brown (76-110), а не светло-серые (210-230) как VLM сообщал в 0.2.4.
Только Marble Table placement 1 даёт bright cream (237,208,169).
Возможные причины:
1. Placement точка попадает на тень под Marble объектом, а не на
   мраморную поверхность.
2. Marble декорации имеют большую dark base + light top, и sampling
   radius 4 wu центрирован на нижней части.

**Что закроет KI-12:** manual калибровка через `--calibration` с 3+
anchors + больший `--sample-radius-wu` (8-12), либо опция
`--sample-offset-y-wu` для смещения sampling window вверх (на bright top
surface Marble). Шаблон: `scripts/calibrations/<stem>.json` с 3+ anchors.

### KI-13 (0.2.7) — Drawing primitives не проверены в игре

Реализованы 5 примитивов в `src/hideout_art/primitives.py` и применены к
`чистый холст.hideout` (см. `download/чистый холст с примитивами.hideout`).
Открывается в парсере, round-trip OK, все 52 art-размещения в пределах
`CANAL_HIDEOUT_BOUNDS`. Но визуальная проверка в самом PoE2 ещё не
проведена. Подвопросы:
- (a) **Sprite overlap.** При spacing = `min_spacing_wu` из каталога
  видимые спрайты могут перекрываться, скрывая форму. Если фигуры
  сливаются в кашу → увеличить `--spacing-override` до 1.5× catalog min.
- (b) **Long Grass visibility.** Травяные декорации имеют alpha-подобный
  спрайт — могут быть плохо видны на полу. Если вертикальные линии
  невидимы → заменить на `Slender Seedling` или `Maraket Rubble`.
- (c) **Thick line thickness cap.** Толщина `thick_line_with_contours`
  ограничена min spacing декорации fill: при `thickness < min_spacing`
  заливка содержит ≤1 ряд точек. Для более толстых линий использовать
  декорации с малым spacing (`Long Grass` sp=13.3, `Maraket Rubble`
  sp=13.6) или увеличить `thickness` до 2-3× spacing.
- (d) **Sprite bounds (KI-10).** Placement footprint ≠ sprite bounds —
  видимый размер декорации может превышать 1 тайл. Для плотных фигур
  нужны внутриигровые замеры.

**Что закроет KI-13:** импорт `чистый холст с примитивами.hideout` в
игру, скриншот, верификация что все 5 фигур узнаваемы. При проблемах —
тюнить `--spacing-override`, заменять декорации, увеличивать размеры.

## Что улучшать дальше (не в этой итерации)

- **Manual calibration JSON для каждого скриншота.** Auto-calibration
  достаточно точна, но для Marble-серии (KI-12) нужна manual калибровка
  с интерактивным выбором anchor точек. Закроет KI-12.
- **Multi-pass: outline + fill для img2hideout.** Сначала контур, потом
  заливка — узнаваемость фигур сильно вырастет. Реализуется в
  `img2hideout.py` через `outline_color` + двухпроходной рендер. На
  контуре — только small-декорации (1 тайл), на fill — средние/крупные.
  Использует `DECORATION_FOOTPRINT_CATALOG`. Drawing primitives (0.2.7)
  — это предтеча: `thick_line_with_contours` уже реализует outline+fill
  паттерн, его логику можно обобщить.
- **Drawing primitives v2.** После визуальной проверки KI-13: добавить
  `arc`, `bezier_curve`, `polygon`, `text` (через bitmap font). Сейчас
  только базовые 5 фигур.
- **Замер sprite bounds.** Расширить каталог полем `sprite_bounds_wu`
  отдельно от placement footprint. Закроет KI-10 и улучшит точность
  drawing primitives.
- **Новая peach/tan декорация для 'skin' role.** Найти в другом убежище
  декорацию с RGB ~ (228,200,178). Закроет KI-2.
- **Поддержка нескольких убежищ.** Сейчас `NAMED_BOUNDS` содержит только
  `canal`. Добавлять новые по мере появления экспортов.
- **SVG / Lua экспорт** — для ручной доводки.

## Базовые принципы при правках

1. **Сначала в STATUS.md, потом фикс.** Новый баг → новый KI-N → потом код.
2. **Никогда не ломать существующие тесты.** Все новые опции — opt-in.
3. **Никогда не выдумывать хеши.** Нет в `KNOWN_HASHES` → помечаем unknown.
4. **RGB-значения — с указанием источника и даты.** VLM-замеры помечать
   `VLM <version>, <date>`. Pixel-sampled — `PIXEL <version>, <date>`.
   Если VLM и PIXEL конфликтуют — доверять PIXEL (KI-11 закрыт).
5. **Документация короткая.** Этот файл — не больше 130 строк.
6. **Каталог размеров — sync с исходниками.** При добавлении размещений
   в `исходники/` перезапускать `scripts/measure_decorations.py` и
   обновлять `DECORATION_FOOTPRINT_CATALOG`. Тест
   `test_sample_counts_match_real_exports` упадёт при рассинхроне.
7. **Drawing primitives — только ART_TYPES.** Никогда не использовать
   functional-объекты в примитивах (см. `safe_spacing` в `primitives.py`
   — он валидирует).
